# Weibo World Cup Engagement Analysis

This project collects public Weibo search result data for the keyword **"世界杯"** and analyzes user engagement metrics such as likes, comments, reposts, publishing sources, and overall post popularity.

The project demonstrates a complete data workflow from dynamic web scraping to data cleaning and interactive visualization.

## Project Overview

The main goal of this project is to build an end-to-end data pipeline:

```text
Weibo search pages
→ Playwright web scraping
→ CSV data export
→ pandas data cleaning
→ advertisement filtering
→ engagement analysis
→ Plotly interactive HTML dashboard
```

## Features

- Scrape public Weibo search result pages with Playwright
- Handle dynamic page loading
- Support manual login before scraping when required
- Extract structured post data
- Save successful records and failed records separately
- Remove duplicate posts
- Filter advertisement and noisy data
- Clean engagement metrics with pandas
- Calculate a custom hot score
- Generate an interactive Plotly HTML report
- Display multiple charts in a dashboard-style layout

## Project Structure

```text
weibo-worldcup-engagement-analysis
├── scraper
│   └── weibo_scraper.py
├── data
│   ├── raw_weibo.csv
│   └── failed_weibo.csv
├── output
│   └── weibo_dynamic_analysis.html
├── weibo_analysis.py
├── requirements.txt
└── README.md
```

## Data Fields

The scraper extracts the following fields from each Weibo post:

| Field | Description |
|---|---|
| username | Weibo account name |
| content | Post content |
| publish_time | Publish time of the post |
| source | Publishing source |
| repost_count | Number of reposts |
| comment_count | Number of comments |
| like_count | Number of likes |
| page | Search result page number |
| item_index | Item index on the page |
| mid | Weibo post ID |
| scraped_at | Scraping timestamp |

## Advertisement Filtering

During scraping, some promoted posts or advertisements may appear in the search results.

These records can distort the analysis because advertisement posts may have unusually high engagement numbers.  
To improve data quality, this project filters advertisement records using:

- Advertisement label elements in the page structure
- Source-area text such as advertisement indicators
- Additional keyword-based filtering during data analysis

This helps keep the final dataset more focused on normal public Weibo posts.

## Data Analysis

The analysis script uses pandas to clean and process the scraped data.

Main analysis steps include:

- Removing duplicate records
- Handling missing values
- Converting engagement columns to numeric values
- Categorizing publishing sources
- Calculating total likes, comments, and reposts
- Creating a custom hot score

The hot score is calculated as:

```python
hot_score = like_count + comment_count * 2 + repost_count * 3
```

Comments and reposts are given higher weights because they usually represent stronger user engagement than simple likes.

## Visualizations

The Plotly HTML report includes:

1. Top 10 posts by likes
2. Top 10 posts by comments
3. Top 10 posts by reposts
4. Publishing source category distribution
5. Top 10 posts by hot score
6. Engagement comparison of top posts

The final report is exported as:

```text
output/weibo_dynamic_analysis.html
```

Open this file in a browser to view the interactive dashboard.

## Tech Stack

- Python
- Playwright
- pandas
- Plotly
- HTML / CSS
- CSV

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Or install them manually:

```bash
pip install pandas plotly playwright
playwright install
```

## Usage

### 1. Run the scraper

```bash
python scraper/weibo_scraper.py
```

A browser window will open.  
If Weibo requires login, complete the login manually in the browser.  
After the search result page is loaded, return to the terminal and press Enter.

The scraper will generate:

```text
data/raw_weibo.csv
data/failed_weibo.csv
```

### 2. Run the analysis

```bash
python weibo_analysis.py
```

The analysis script will generate:

```text
output/weibo_dynamic_analysis.html
```

Open the HTML file in a browser to view the interactive report.

## Notes

This project only collects publicly visible search result data.

It does not bypass login systems, CAPTCHA, access restrictions, or platform security mechanisms.  
If login is required, the user completes it manually in the browser.

The project is designed for learning and portfolio demonstration purposes.

## What I Learned

Through this project, I practiced:

- Scraping dynamic web pages
- Handling login redirects manually
- Extracting structured data from complex HTML
- Filtering advertisements and noisy records
- Cleaning CSV data with pandas
- Designing engagement metrics
- Building interactive data reports with Plotly
- Creating a complete scraping-to-analysis workflow