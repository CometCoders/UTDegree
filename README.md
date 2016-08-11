# UTDegree

Get more or less complete degree plans from the UTD Course Catalog in JSON.

## Dependencies

* python 2.7.10
* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)

## Usage

Go to [catalog.utdallas.edu](http://catalog.utdallas.edu/) and locate your plan. Use its url in the space below.

`python utdegree.py <url>`

## Example

(Will take a few seconds)

![Imgur](http://i.imgur.com/ZYzuhSQ.gif)

## What do I do with these plans?

Write a program that helps you graduate as quickly as possible with a custom courseload.

## Known Issues

* Only gets the first plan from pages with multiple degree plans (Will fix).
* The data isn't all there on the catalog, nor the formatting consistent. So it's best to save these plans to a file, cross-check them with the catalog, and fill in whatever is missing/incorrect (Takes maybe 5 mins. Much quicker than writing down the entire plan yourself).

## License 

Copyright (c) 2016 Tushar Rakheja (MIT)
