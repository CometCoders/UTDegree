"""
Get more or less complete degree plans from catalog.utdallas.edu

Usage: python utdegree.py <url>'
"""

import json
import re
import sys
import urllib
from bs4 import BeautifulSoup, NavigableString


"""
Definitions:

0. prereq (pr) - A prereq of a course A is a course that must be taken before A, as listed in the catalog.
   (i.e. a prereq of a prereq is not `defined` to be a prereq, even though it is one).

1. weak coreq (wc) - A weak coreq of a course A is a course that must be taken before or along with A. 

2. strict coreq (sc) - A strict coreq of a course A is a course that must be taken along with A.
   (The strict coreq relation is an equivalence relation. For the purposes of optimizing a degree plan,
    strict coreqs can be treated as a single 'compound course').

4. Option - A course that may be taken in place of a different course.

5. Mandate - A list of options, one of which must be taken.

6. Completing a mandate - Taking at least one course in the mandated list.

7. A Requirement is a list of mandates, all of which must be completed.

8. A Course - A list containing
    a. number of a course.
    b. its pr requirement.
    c. its wc requirement.
    d. its sc requirement.
"""

course_num_pattern = re.compile('[A-Z]{2,4} [0-9]{4}')                     # Every course number has a prefix and a number.

class Course:
    """Encapsulates the blueprint of a course."""
    def __init__(self, tag):
        """
        Initialize self using the tag that contains the data.

        Get the course num. If it matches the pattern for a course num,
        use the tag to extract pre-req and co-req data out of the tag's
        title.
        """
        self.num = unicode(tag.string).encode('utf-8')
        self.taken = False
        self.sem = 0
        self.prereqs = []
        self.wcoreqs = []
        self.scoreqs = []
        if not course_num_pattern.match(self.num):    # Sometimes a requirement is listed, but no course to fulfil it.
            pass                                      # In that case, don't try to get the prereqs and coreqs.
        else:
            self.get_prereqs(tag)
            self.get_wcoreqs(tag)
            self.get_scoreqs(tag)

    def get_prereqs(self, tag):
        """Get the course's prereqs from the tag's title attribute."""
        raw = re.findall('Prerequisite[s]?:(.*)Prerequisite[s]? or Corequisite[s]?:', tag['title'])
        if len(raw) < 1: # The course has no weak coreqs.
            raw = re.findall('Prerequisite[s]?:(.*)Corequisite[s]?:', tag['title'])
            if len(raw) < 1: # The course has no strong coreqs either.
                raw = re.findall('Prerequisite[s]?:(.*)\(Same as.*\)', tag['title'])
                if len(raw) < 1: # The course is not the same as another course.
                    raw = re.findall('Prerequisite[s]?:(.*)\([0-9]-[0-9]\)', tag['title'])
                    if len(raw) < 1: # The course has no prereqs either.
                        return
        self.build_and_add_mandates(self.prereqs, raw)   
            
    def get_wcoreqs(self, tag):
        """Get the course's wcoreqs from the tag's title attribute."""
        raw = re.findall('Prerequisite[s]? or Corequisite[s]?:(.*)\. Corequisite[s]?:', tag['title'])
        if len(raw) < 1: # The course has no strong coreqs.
            raw = re.findall('Prerequisite[s]? or Corequisite[s]?:(.*)\(Same as.*\)', tag['title'])
            if len(raw) < 1: # The course is not the same as another course.
                raw = re.findall('Prerequisite[s]? or Corequisite[s]?:(.*)\([0-9]-[0-9]\)', tag['title'])
                if len(raw) < 1: # The course has no weak coreqs either.
                    return
        self.build_and_add_mandates(self.wcoreqs, raw)
        
            
    def get_scoreqs(self, tag):
        """Get the course's wcoreqs from the tag's title attribute."""
        raw = re.findall('\. Corequisite[s]?:(.*)\(Same as.*\)', tag['title'])
        if len(raw) < 1: # The course is not the same as another course.
            raw = re.findall('\. Corequisite[s]?:(.*)\([0-9]-[0-9]\)', tag['title'])
            if len(raw) < 1: # The course has no strong coreqs.
                return
        self.build_and_add_mandates(self.scoreqs, raw)

    def build_and_add_mandates(self, lst, raw):
        """Process mandates from a raw string and add them to lst."""
        mandates = raw[0].split(' and ')
        for mandate in mandates:
            new_mandate = []
            options = mandate.split(' or ')
            for option in options:
                if len(re.findall('>(.*)<', option)) > 0:
                    new_mandate.append(re.findall('>(.*)<', option)[0])
                else:
                    new_mandate.append(option)
            if (len(new_mandate) != 0):
                lst.append(new_mandate)
        
course_list = []
course_soup = BeautifulSoup(urllib.urlopen(sys.argv[1]).read(), 'html.parser')

"""
* We only want the:
* 1. Core Curriculum Requirements, and the
* 2. Major Requirements (w/o electives)

* These specific headings (which are not really headings), have the structure:

<p class="cat-reqa ... " ... >
    I. Core Curriculum Requirements: ...
    <a>
    </a>
</p>
.
.
.
<p class="cat-reqa ... " ... >
    II. Major Requirements: ...
    <a>
    </a>
</p>

* Course info is also found in <p> tags. The structure of these tags is:

<p class="cat-reqi ... catreq-cont">
    or
    <a ... >
        `Course Name`
    </a>
</p>

* `catreq-cont` indicates an option between two requirements.
* The 'or' NavigableString will only be a child of <p> if catreq-cont is a class.
* These `cat-reqi` classified <p> tags containing course info are siblings of the
  `cat-reqa` classified <p> tags containing the requirement headings, with ordinality >= 2.
"""

for p in course_soup.find_all('p', class_='cat-reqa'):
    if len(re.findall('^\s*I.', p.contents[0])) > 0:
        p = p.next_sibling
        while isinstance(p, NavigableString):
            p = p.next_sibling
        while 'cat-reqa' not in p['class']:
            if 'catreq-cont' in p['class']:
                a = p.contents[1]
                while not unicode(a.string) or unicode(a.string).isspace():
                    a = a.next_sibling
                course_list[len(course_list) - 1].append(Course(a))
            elif 'cat-reqi' in p['class']:
                a = p.contents[0]
                while not unicode(a.string) or unicode(a.string).isspace():
                    a = a.next_sibling
                course_list.append([Course(a)])
            p = p.next_sibling
            while isinstance(p, NavigableString):
                p = p.next_sibling
        
    if len(re.findall('^\s*II.', p.contents[0])) > 0:
        p = p.next_sibling
        while isinstance(p, NavigableString):
            p = p.next_sibling
        if 'cat-reqg' in p['class'] and len(re.findall('[e|E]lectives', p.string)) > 0:
            break
        while 'cat-reqa' not in p['class']:
            if 'catreq-cont' in p['class']:
                a = p.contents[1]
                while not unicode(a.string) or unicode(a.string).isspace():
                    a = a.next_sibling
                course_list[len(course_list) - 1].append(Course(a))
            elif 'cat-reqi' in p['class']:
                a = p.contents[0]
                while not unicode(a.string) or unicode(a.string).isspace():
                    a = a.next_sibling
                course_list.append([Course(a)])
            p = p.next_sibling
            while isinstance(p, NavigableString):
                p = p.next_sibling

print json.dumps(course_list, default=lambda o: o.__dict__, sort_keys=True, indent=4)

