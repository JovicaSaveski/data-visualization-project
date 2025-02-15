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

# Load both CSV files
try:
    df1 = pd.read_csv('sequential_car_listings.csv')
    df2 = pd.read_csv('sequential_car_listings2.csv')
    print(f"Loaded data shapes: df1={df1.shape}, df2={df2.shape}")
    
    # Concatenate the dataframes
    df = pd.concat([df1, df2], ignore_index=True)
    print(f"Combined shape: {df.shape}")
    
except Exception as e:
    print(f"Error loading CSV files: {e}")
    exit(1)

# Remove duplicates based on URL
df = df.drop_duplicates(subset='url', keep='first')
print(f"Shape after removing duplicates: {df.shape}")

# Only fill missing or zero prices
df['price_numeric'] = df.apply(
    lambda row: extract_price(row['description']) if (pd.isna(row['price_numeric']) or row['price_numeric'] == 0) else row['price_numeric'],
    axis=1
)

# Basic cleaning
df['year'] = pd.to_numeric(df['year'], errors='coerce')
df['views'] = pd.to_numeric(df['views'], errors='coerce')

# Standardize currency to EUR if possible
df['currency'] = df['currency'].fillna('EUR')
df['currency'] = df['currency'].str.upper()

# Save the cleaned data
df.to_csv('sequential_car_listings_cleaned.csv', index=False)
print("Data cleaning complete. Cleaned data saved to 'sequential_car_listings_cleaned.csv'")

# Print some statistics
print("\nBasic statistics:")
print(f"Total listings: {len(df)}")
print(f"Unique years: {df['year'].nunique()}")
print(f"Average price: {df['price_numeric'].mean():.2f}")
print(f"Missing prices: {df['price_numeric'].isna().sum()}")