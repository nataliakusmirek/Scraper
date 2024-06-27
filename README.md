# Web Scraper

This Python-based web scraper is designed to crawl and extract content from websites, including text and images, while managing URLs for further exploration.

## Features

- **URL Management**: Utilizes priority queue to manage URLs for scraping, ensuring efficient exploration of website links.
- **Text Extraction**: Extracts and saves text content from HTML pages, suitable for analysis or AI model training.
- **Image Handling**: Downloads and resizes images from web pages for storage or further processing.
- **Threaded Processing**: Implements multithreading for concurrent URL processing, enhancing efficiency.
- **Error Handling**: Manages HTTP errors and retries, with logging for detailed error reporting.
- **User-Agent Customization**: Includes a customizable User-Agent header for requests.

## Requirements

- Python 3.x
- Required Python packages (install using `pip`):
  - `requests`
  - `beautifulsoup4`
  - `Pillow`

Install dependencies using:

```bash
pip install requests beautifulsoup4 Pillow
```

## Usage

1. Clone or download the repository:

```bash
git clone https://github.com/yourusername/web-scraper.git
cd web-scraper
```

2. Modify the `main()` function in `scraper.py` to specify the starting URL:

```python
if __name__ == "__main__":
    scraper = Scraper()
    scraper.main()
```

3. Run the scraper:

```bash
python scraper.py
```

4. Monitor the scraping process through logging messages. Data will be saved in the `pages/` directory for text content and `images/` directory for resized images.

## Applications

- **Data Collection**: Gather structured data for analysis or research purposes.
- **Content Aggregation**: Build datasets for machine learning or natural language processing tasks.
- **Monitoring**: Automate periodic scraping tasks for updated information.

## Notes

- Ensure compliance with website terms of service and legal requirements when scraping.
- Customize the scraper for specific websites by adjusting URL handling or content extraction methods.
