import pandas as pd
import numpy as np
from datetime import datetime
import glob

def load_and_combine_data(file_pattern):
    """Load and combine multiple CSV files"""
    all_files = glob.glob(file_pattern)
    df_list = []
    
    for file in all_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            df_list.append(df)
        except Exception as e:
            print(f"Error loading {file}: {str(e)}")
    
    return pd.concat(df_list, ignore_index=True)

def clean_data(df):
    """Main data cleaning function"""
    # Remove duplicates
    df = df.drop_duplicates(subset=['url', 'title', 'price_value'], keep='last')
    
    # Convert data types
    numeric_cols = ['price_value', 'mileage_start', 'mileage_end', 'year', 'views']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    # Handle missing values
    df = handle_missing_values(df)
    
    # Create calculated columns
    df = create_calculated_columns(df)
    
    # Clean text fields
    text_cols = ['title', 'description', 'fuel_type', 'transmission']
    df[text_cols] = df[text_cols].apply(lambda x: x.str.strip().str.title())
    
    return df

def handle_missing_values(df):
    """Handle missing data based on column type"""
    # Numeric columns: fill with median
    numeric_cols = ['price_value', 'mileage_start', 'year']
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())
    
    # Categorical columns: fill with mode
    cat_cols = ['fuel_type', 'transmission', 'seller_type']
    for col in cat_cols:
        df[col] = df[col].fillna(df[col].mode()[0])
    
    # Other columns
    df['description'] = df['description'].fillna('No description')
    df['color'] = df['color'].fillna('Unknown')
    
    return df

def create_calculated_columns(df):
    """Create derived metrics"""
    current_year = datetime.now().year  # Will use 2025 based on your context
    
    df['car_age'] = current_year - df['year']
    df['price_per_year'] = df['price_value'] / df['car_age'].replace(0, 1)
    df['mileage_per_year'] = df['mileage_start'] / df['car_age'].replace(0, 1)
    
    # Categorization
    df['price_category'] = pd.cut(df['price_value'],
                                bins=[0, 5000, 10000, 20000, np.inf],
                                labels=['Budget', 'Mid-range', 'Premium', 'Luxury'])
    
    return df

def save_clean_data(df, output_file):
    """Save cleaned data with proper formatting"""
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Saved cleaned data to {output_file} with {len(df)} records")

if __name__ == "__main__":
    # Configuration
    INPUT_PATTERN = "parallel_car_listings*.csv"
    OUTPUT_FILE = "cleaned_car_listings.csv"
    
    # Execution pipeline
    combined_df = load_and_combine_data(INPUT_PATTERN)
    cleaned_df = clean_data(combined_df)
    save_clean_data(cleaned_df, OUTPUT_FILE)
