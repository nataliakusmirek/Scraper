import requests
import re
import csv
import time
from bs4 import BeautifulSoup
from collections import Counter
from queue import PriorityQueue
import threading
import logging
from PIL import Image
from io import BytesIO
import os
from urllib.parse import urlparse
from urllib.parse import urljoin


class Scraper:
    def __init__(self):
        self.visited_urls = set()
        self.count = 0
        self.word_counter = Counter()
        self.url_queue = PriorityQueue()
        self.lock = threading.Lock()  # For thread safety

    def get_html(self, url, retries=1, delay=5):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200: #and url not in self.visited_urls:
                return response.content
            elif response.status_code in [503, 429]:
                logging.warning(f"Received {response.status_code} status code. Retrying after delay.")
                time.sleep(delay)
                if retries > 0:
                    return self.get_html(url, retries - 1, delay)
                else:
                    logging.warning(f"Retry limit exceeded for {url}. Moving on to next URL.")
                    return None
            else:
                logging.error(f"Failed to fetch HTML from {url}. Status code: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching HTML from {url}: {e}, moving onto next URL.")
            retries -= 1
            return None
    
    def save_text(self, url, text_content):
        with open(f'pages/{self.count}_content.txt', 'w', encoding='utf-8') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([url, text_content])

    def extract_content(self, url, output_dir):
        html_content = self.get_html(url)
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            # Extract text content from article
            text_content = "\n".join(tag.get_text() for tag in soup.find_all(['p', 'span', 'alt', 'title', 'h1', 'h2', 'h3', 'a']))
            with self.lock:
                self.count += 1
                with open(f'{output_dir}/{self.count}_content.txt', 'w', encoding='utf-8') as file:
                    file.write(text_content)
                self.save_text(url, text_content)
            logging.info(f"Page content extracted and saved to {output_dir}/{self.count}_content.txt")
        else:
            logging.error(f"Failed to fetch HTML from {url}")

    def download_and_resize_image(self, base_url, img_url):
        try:
            if img_url:
                img_url = urljoin(base_url, img_url)
            else:
                return
            response = requests.get(img_url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                if img.mode in ['RGBA', 'P']:
                    img = img.convert('RGB')
                img = img.resize((256, 256))
                with self.lock:
                    self.count += 1
                    img.save(f'images/{self.count}.jpg', 'JPEG', quality=95)
            else:
                logging.error(f"Failed to download image from {img_url}. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Failed to download and resize image: {e}")
    
    def scrape_page(self, url, retries=1, delay=5):
        html_content = self.get_html(url, retries=retries, delay=delay)
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            title_tags = soup.find_all(['h1', 'h2', 'h3', 'a'])
            if title_tags:
                title = title_tags[0].get_text().lower()
                # Extract text content from page to split into individual words
                text = " ".join(tag.get_text() for tag in soup.find_all(['p', 'span', 'alt', 'title', 'class', 'h1', 'h2', 'h3']))
                # Clean the text
                cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
                # Tokenize the text
                words = cleaned_text.split()
                self.word_counter.update(words)
                # Write name and link to CSV to store URLs
                article_name = title_tags[0].get_text()
                with open('links.csv', 'a', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow([url])
                # Extract and save full article text for AI model training
                output_dir = f'pages'
                os.makedirs(output_dir, exist_ok=True)
                self.extract_content(url, output_dir)
                # Extract and save images
                for img in soup.find_all('img'):
                    img_url = img.get('src')
                    self.download_and_resize_image(url, img_url)
                logging.info(f"Scraped page: {url}")
            else:
                logging.warning(f"No items found for page: {url}")
            # Find all links on the page and scrape subpages
            for link in soup.find_all(['a'], href=True):
                self.enqueue_url(url, link.get('href'))
        else:
            if not html_content:
                if retries > 0:
                    logging.error(f"Failed to scrape page: {url}. Retrying...")
                    self.scrape_page(url, retries=retries - 1, delay=delay)
                else:
                    logging.error(f"Failed to scrape page: {url}. Moving on to the next link.")
    
    def enqueue_url(self, base_url, link):
        if not link.startswith(('http://', 'https://')):
            link = urljoin(base_url, link)
        if link.startswith('http://login', 'http://enable', 'mailto', 'tel', 'javascript'):
            return
        if link.startswith('#'):
            return
        if link.startswith('www'):
            link = f"https://{link}"
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc
        if link.startswith('/'):
            link = urljoin(f"https://{domain}", link)
        if link not in self.visited_urls:
            self.url_queue.put((1, link))
    
    def print_queue(self):
        queue = list(self.url_queue.queue)
        print("Current URL Queue:")
        for priority, url in queue:
            print(f"Priority: {priority}, URL: {url}")
    
    def process_queue(self):
        while True:
            priority, url = self.url_queue.get()
            with self.lock:
                if url in self.visited_urls:
                    self.url_queue.task_done()
                    continue
                self.visited_urls.add(url)
            time.sleep(30)
            self.scrape_page(url)
            self.url_queue.task_done()
            if self.url_queue.empty():
                break
            self.print_queue()

    def main(self):
        print("Enter the URL of the site to build a wardrobe from:")
        url = input().strip()

        # Start the scraping
        logging.basicConfig(level=logging.INFO)
        self.url_queue.put((0, url))
        self.process_queue()

        # Print queue every 30 seconds until empty
        while not self.url_queue.empty():
            time.sleep(30)
            self.print_queue()
        
        # Create worker threads for efficiency
        num_threads = 14
        for _ in range(num_threads):
            thread = threading.Thread(target=self.process_queue)
            thread.daemon = True
            thread.start()
        self.url_queue.join()
        print("-" * 40)
        logging.info("All URLs of provided website have been scraped. Data has been exported.")

if __name__ == "__main__":
    scraper = Scraper()
    scraper.main()


    # scraper should run periodically
