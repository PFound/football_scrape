# FootballScraper

Football Scraper is a Python-based project that scrapes football match data from the English Championship and retrieves match links from a the ESPN website. It provides an efficient and easy-to-use way to collect football match data for analysis. 

**I have already found that the data seems to be at odds with other sources, but the data is correct as the website displays it.**

## Features

- Scrape match links and store them in a file for future use
- Generate a list of dates for the football season
- Retrieve match data using BeautifulSoup and requests

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/football-data-scraper.git
```

2. Change into the project directory:

```bash
cd football-data-scraper
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

I have started some analysis in the FootballScraper_App.py file so to demonstrate the way to use the code.

```python
python FootballScraper_App.py
```

## Configuration

- `config.base_url`: Base URL of the website being scraped
- `config.url`: URL containing the date placeholder
- `config.date_placeholder`: Placeholder string for the date
- `config.data_fld`: Directory where the match links file is stored

## Contributing

Feel free to submit pull requests or raise issues to help improve the project.

## License

This project is licensed under the MIT License.
