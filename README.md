# FoxNewsScraperParser
## Background
This repository is designed for scraping and parsing articles and images
from ***https://www.foxnews.com/*** with the angular API. This repository
is a part of data science project and the data will be used for text analysis.
## Functions
### foxnewsScraperParser.py
This file includes some global utility functions, and two classes  
***Scraper*** and ***Parser***
* ***Scraper***: Scrapes the meta-information of articles published in each day, which includes
  the title, the description, the publishing time, the article url and the images url. The
  meta-information is saved at a CSV file, which includes all the information of articles
  in one day.

* ***Parser***: Parses and downloads the articles, HTMLs and images from the urls of
the summary file.


### main.py
This file includes a sample test. Here are the sample parameters:
* **start_date**: 2020.04.01
* **end_date**: 2020.04.01
* **key word**: the
* **logger**: ./output.log

Sample results are saved at ***./summary/*** and ***./Content*** respectively
