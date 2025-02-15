import re

def clean_price(price_str):
    return int(re.sub(r'[^\d]', '', price_str)) if price_str else 0

def validate_mileage(mileage_str):
    if '-' in mileage_str:
        return sum(map(int, re.findall(r'\d+', mileage_str))) // 2
    return int(re.sub(r'[^\d]', '', mileage_str))