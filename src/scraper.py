import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import random
from fake_useragent import UserAgent
from urllib.parse import urljoin

BASE_URL = "https://www.pazar3.mk"

# Updated selectors based on individual listing page structure
SELECTORS = {
    'title': 'h1.ci-margin-b-10',
    'price': 'span.actual-price',
    'details_container': 'div.tags-area',
    'detail_item': 'a.tag-item',
    'image': 'img.lazyload',
    'description': 'div.longDescription',
    
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
            'Ad type': 'listing_type'
        }

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

def main():
    all_data = []
    listing_urls = [
    "https://www.pazar3.mk/ad/6308847",
    "https://www.pazar3.mk/ad/6195008",
    "https://www.pazar3.mk/ad/6346988",
    "https://www.pazar3.mk/ad/6346934",
    "https://www.pazar3.mk/ad/6346905",
    "https://www.pazar3.mk/ad/6333151",
    "https://www.pazar3.mk/ad/6308268",
    "https://www.pazar3.mk/ad/6346596",
    "https://www.pazar3.mk/ad/6346515",
    "https://www.pazar3.mk/ad/6346520",
    "https://www.pazar3.mk/ad/6346616",
    "https://www.pazar3.mk/ad/6346665",
    "https://www.pazar3.mk/ad/6346619",
    "https://www.pazar3.mk/ad/5574587",
    "https://www.pazar3.mk/ad/6346196",
    "https://www.pazar3.mk/ad/6138490",
    "https://www.pazar3.mk/ad/6346034",
    "https://www.pazar3.mk/ad/6161569",
    "https://www.pazar3.mk/ad/6333696",
    "https://www.pazar3.mk/ad/6228159",
    "https://www.pazar3.mk/ad/6307394",
    "https://www.pazar3.mk/ad/6332375",
    "https://www.pazar3.mk/ad/4752966",
    "https://www.pazar3.mk/ad/6308328",
    "https://www.pazar3.mk/ad/6307001",
    "https://www.pazar3.mk/ad/6310605",
    "https://www.pazar3.mk/ad/4738834",
    "https://www.pazar3.mk/ad/4759540",
    "https://www.pazar3.mk/ad/6334026",
    "https://www.pazar3.mk/ad/6205280",
    "https://www.pazar3.mk/ad/6333094",
    "https://www.pazar3.mk/ad/6332831",
    "https://www.pazar3.mk/ad/6333091",
    "https://www.pazar3.mk/ad/6333005",
    "https://www.pazar3.mk/ad/6172718",
    "https://www.pazar3.mk/ad/6332468",
    "https://www.pazar3.mk/ad/6321765",
    "https://www.pazar3.mk/ad/6321662",
    "https://www.pazar3.mk/ad/6309840",
    "https://www.pazar3.mk/ad/6321764",
    "https://www.pazar3.mk/ad/6321736",
    "https://www.pazar3.mk/ad/6111914",
    "https://www.pazar3.mk/ad/5836982",
    "https://www.pazar3.mk/ad/5226748",
    "https://www.pazar3.mk/ad/6310718",
    "https://www.pazar3.mk/ad/6310671",
    "https://www.pazar3.mk/ad/6228315"
]
    
    for url in listing_urls:
        print(f"Scraping {url}")
        data = scrape_listing(url)
        if data:
            all_data.append(data)
        time.sleep(random.uniform(1, 3))
        
    if all_data:
        df = pd.DataFrame(all_data)
        # Rename Macedonian fields to English
        
        df.rename(columns=field_mapping, inplace=True)
        
        # Save with Macedonian encoding support
        df.to_csv('car_listings.csv', index=False, encoding='utf-8-sig')
        print(f"Successfully saved {len(df)} listings")

if __name__ == "__main__":
    main()
