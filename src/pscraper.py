import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import random
from fake_useragent import UserAgent
from urllib.parse import urljoin
import threading
from tenacity import retry, stop_after_attempt, wait_random_exponential
import csv
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://www.pazar3.mk"

# Updated selectors based on individual listing page structure
SELECTORS = {
    'title': 'h1.ci-margin-b-10',
    'price': 'span.actual-price',
    'details_container': 'div.tags-area',
    'detail_item': 'a.tag-item',
    'image': 'img.lazyload',
    'description': 'div.longDescription',
    'price_container': 'h4.ci-text-success',
    'price_value': 'span.format-money-int[value]',
    'price_currency': 'span.format-money-currency'
    
}
field_mapping = {
            'Condition': 'condition',
            'Year': 'year',
            'Gear Box': 'transmission',
            'Mileage': 'mileage',
            'Fuel': 'fuel_type',
            'Registration': 'registration',
            'Advertised by': 'seller_type',
            'Location': 'location',
            'Color': 'color',
            'Manufacturer': 'manufacturer',
            'Model': 'model',
            'Ad type': 'listing_type',
            'price_display': 'price',
            'price_value': 'price_numeric',
            'price_currency': 'currency'
        }

page_number = '1'

def get_headers():
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept-Language': 'mk-MK,en-US;q=0.7',
        'X-Requested-With': 'XMLHttpRequest'
}

def safe_extract(soup, selector, attr=None):
    try:
        element = soup.select_one(selector)
        if element:
            if attr and attr == 'text':
                return element.get_text(strip=True)
            if attr:
                return element[attr]
            return element
        return None
    except Exception:
        return None

def scrape_listing(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Core metadata
        data = {
            'title': safe_extract(soup, 'h1.ci-text-base', 'text'),
            'price': clean_price(safe_extract(soup, 'span.actual-price', 'text')),
            'description': safe_extract(soup, 'div.description-area', 'text'),
            'url': url,
            'images': [img['data-src'] for img in soup.select('img.lazyload') if img.has_attr('data-src')],
            
            # Address components
            'address': safe_extract(soup, '.display-ad-address', 'text'),
            'coordinates': extract_coordinates(soup),
            
            # Publication info
            'publish_date': safe_extract(soup, '.published-date', 'text'),
            'publish_time': safe_extract(soup, '.published-time', 'text'),
            'views': safe_extract(soup, '.views-number span', 'text'),
            
            # Contact information
            'phone': safe_extract(soup, 'a[href^="tel:"]', 'text'),
            'has_message_button': bool(soup.select_one('[data-target="#contactModal"]'))
        }

        # Extract and process tags-area
        tags = soup.select('div.tags-area a.tag-item')
        for tag in tags:
            key = safe_extract(tag, 'span', 'text').replace(':', '').strip()
            value = safe_extract(tag, 'bdi', 'text')
            if key and value:
                data[key] = value
                
        

        # Enhanced field processing
        data.update({
            'price_value': parse_price_value(data.get('price', '')),
            'price_currency': parse_price_currency(data.get('price', '')),
            'mileage_start': parse_mileage_range(data.get('Километража', ''), 'start'),
            'mileage_end': parse_mileage_range(data.get('Километража', ''), 'end'),
            'manufacturer': data.get('Производител') or data.get('Manufacturer'),
            'model': data.get('Модел') or data.get('Model'),
            'registration_date': parse_registration_date(data.get('Регистрација', ''))
        })
        
        price_info = extract_price(soup)
        data.update({
            'price_value': price_info['price_value'],
            'price_currency': price_info['price_currency'],
            'price_display': price_info['price_display']
        })

        # Convert numeric fields
        conversions = {
            'year': ('Година', int),
            'engine_size': ('Мотор', parse_engine_size),
            'seller_type': ('Огласено од', lambda x: 'Private' if 'Физичко' in x else 'Business')
        }
        
        for field, (source, func) in conversions.items():
            if source in data:
                try:
                    data[field] = func(data[source])
                except (ValueError, TypeError):
                    data[field] = None

        return {field_mapping.get(k, k): v for k, v in data.items() if v is not None}
    
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def extract_coordinates(soup):
    map_link = soup.select_one('a.map[data-target="location"]')
    if map_link and 'data-coords' in map_link.attrs:
        return tuple(map(float, map_link['data-coords'].split(',')))
    return None

def extract_price(soup):
    price_data = {
        'price_value': None,
        'price_currency': None,
        'price_display': None
    }
    
    # Extract numeric value from hidden attribute
    price_value_span = soup.select_one('span.format-money-int[value]')
    if price_value_span:
        price_data['price_value'] = int(price_value_span['value'])
        price_data['price_display'] = price_value_span.get_text(strip=True)
    
    # Extract currency
    currency_span = soup.select_one('bdi.new-price > span:not([class])')
    if currency_span:
        price_data['price_currency'] = currency_span.get_text(strip=True)
    
    # Create combined display format
    if price_data['price_display'] and price_data['price_currency']:
        price_data['price_display'] = f"{price_data['price_display']} {price_data['price_currency']}"
    
    return price_data


def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip() if text else None

def convert_price(value):
    try:
        return float(value.replace(',', '')) if value else None
    except (ValueError, TypeError):
        return None

def safe_extract(soup, selector, attr=None):
    element = soup.select_one(selector)
    if not element:
        return None
    if attr == 'text':
        return element.get_text(strip=True)
    if attr == 'value':
        return element.get('value', '').strip()
    return element.get(attr, '').strip() if attr else element

# Helper functions
def parse_price_value(price_str):
    if not price_str: return None
    return re.sub(r'[^\d.]', '', price_str.split()[0])

def parse_price_currency(price_str):
    if not price_str: return None
    return 'MKD' if 'МКД' in price_str else 'EUR'

def parse_mileage_range(value, type='start'):
    numbers = re.findall(r'\d+', value.replace(' ', ''))
    if not numbers: return None
    try:
        return int(numbers[0] if type == 'start' else numbers[-1])
    except (IndexError, ValueError):
        return None

def parse_registration_date(reg_str):
    try:
        return datetime.strptime(reg_str, '%m/%Y').strftime('%Y-%m') if reg_str else None
    except ValueError:
        return None

def parse_engine_size(value):
    if not value: return None
    return float(re.search(r'\d+\.?\d*', value.replace(',', '.')).group())


def clean_price(price_str):
    if price_str:
        return re.sub(r'[^\d]', '', price_str)
    return None

def parse_mileage(value):
    numbers = re.findall(r'\d+', value)
    return int(''.join(numbers)) if numbers else None

def scrape_search_results(page_number):
    # Construct the filename based on the page number
    filename = f'search_results_page_{page_number}.csv'
    
    # Initialize an empty list to store the search results
    search_results = []
    
    try:
        # Open the CSV file for reading
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            # Create a CSV reader object
            csv_reader = csv.reader(file)
            
            # Skip the header row if your CSV has headers
            next(csv_reader, None)
            
            # Iterate over each row in the CSV
            for row in csv_reader:
                # Join the list of strings into a single string separated by commas
                row_string = ','.join(row)
                # Append the string to the search_results list
                search_results.append(row_string)
                
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return search_results

def main():
    all_data = []

    # Process pages 1 to 12 sequentially
    for page_number in range(13, 23):
        print(f"Processing page {page_number}...")
        listing_urls = scrape_search_results(page_number)  # Get listing URLs for the current page

        # Process each listing in parallel for this page
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scrape_listing, url) for url in listing_urls]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        all_data.append(result)
                except Exception as e:
                    print(f"Error scraping listing: {e}")

        # Optional: add a delay between pages to avoid overwhelming the server
        time.sleep(5)

    # Save the collected data to a CSV file after processing all pages
    if all_data:
        df = pd.DataFrame(all_data).rename(columns=field_mapping)
        df.to_csv('sequential_car_listings2.csv', index=False)

if __name__ == "__main__":
    main()
