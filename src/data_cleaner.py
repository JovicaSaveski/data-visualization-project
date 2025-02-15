import pandas as pd
import numpy as np
import re

def extract_price(text):
    """Extract price from text using various patterns"""
    if pd.isna(text):
        return 0
    
    # Common price patterns in Macedonian listings
    patterns = [
        r'(?:цена|cena|CENA)[:\s]*?(\d+(?:,\d+)?(?:\.\d+)?)',  # Price after цена/cena
        r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:€|eur|EUR)',  # Number before € symbol
        r'(?:цена|cena|CENA)[:\s]*?(\d+)(?:\s*(?:€|eur|EUR))?',  # Just the number after price indicator
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            price = matches[0].replace(',', '')
            try:
                return float(price)
            except ValueError:
                continue
    return 0

# Load the CSV file
try:
    df = pd.read_csv('sequential_car_listings.csv')
    print(f"Loaded data shape: {df.shape}")
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit(1)

# Only fill missing or zero prices
df['price_numeric'] = df.apply(
    lambda row: extract_price(row['description']) if (pd.isna(row['price_numeric']) or row['price_numeric'] == 0) else row['price_numeric'],
    axis=1
)

# Rest of the cleaning code remains the same
...

# Save the cleaned data
df.to_csv('sequential_car_listings_cleaned.csv', index=False)
print("Data cleaning complete. Cleaned data saved to 'sequential_car_listings_cleaned.csv'")