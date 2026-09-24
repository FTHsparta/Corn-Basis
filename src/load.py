import numpy as np
import pandas as pd

def load_cash(cash_path):    
    raw = pd.read_excel(cash_path, sheet_name='CORN', header=None)
    my_slice = raw.iloc[8:, [0, 7, 17, 21]] #grabs the columns we want (date, kansas city, dodge city, garden city)

    renamed_slice = my_slice.rename(columns={0: 'date', 7: 'kansas_city', 17: 'dodge_city', 21: 'garden_city'}) #renames the columns for ease of use
    renamed_slice['date'] = pd.to_datetime(renamed_slice['date'], errors='coerce') #converts the date columns to datetime format and coercing errors

    load_cash_filtered = renamed_slice.dropna(subset=['date']).copy() #deletes the rows that return a null value for the previous line (the cells that aren't dates)

    #converts the remaining columns into numeric values
    load_cash_filtered['kansas_city'] = pd.to_numeric(load_cash_filtered['kansas_city'], errors='coerce')
    load_cash_filtered['dodge_city'] = pd.to_numeric(load_cash_filtered['dodge_city'], errors='coerce')
    load_cash_filtered['garden_city'] = pd.to_numeric(load_cash_filtered['garden_city'], errors='coerce')


    load_cash_filtered[['iso_year', 'iso_week']] = load_cash_filtered['date'].dt.isocalendar()[['year', 'week']].astype(int) #adds iso year and week columns
    expected_start = pd.Timestamp('1988-01-07') #sets expected start date 

    #assertions (checks to make sure the numbers match the results I got by hand)
    assert load_cash_filtered['date'].min() == expected_start, f"Expected start date {expected_start}, but got {load_cash_filtered['date'].min()}" 
    assert (load_cash_filtered['date'].dt.dayofweek == 3).all(), "Data quality error: Not all dates are Thursdays."
    assert load_cash_filtered['kansas_city'].count() == 2015, "kansas city data amount does not match 2015"
    assert load_cash_filtered['dodge_city'].count() == 1906, "dodge city data amount does not match 1906"
    assert load_cash_filtered['garden_city'].count() == 1383, "garden city data amount does not match 1383"

    load_cash_filtered = load_cash_filtered.reset_index(drop = True)
    
    return load_cash_filtered



def load_futures(futures_path):
    raw = pd.read_excel(futures_path, sheet_name = "B", header = None)
    my_slice = raw.iloc[4:, [0, 2, 3, 4, 5, 7, 8] ]
    renamed_slice = my_slice.rename(columns={0: 'date', 2: 'mar', 3: 'may', 4: 'jul', 5: 'sep', 7: 'dec', 8: 'nearby' }) 
    renamed_slice['date'] = pd.to_datetime(renamed_slice['date'], errors='coerce') #converts the date columns to datetime format and coercing errors

    load_future_filtered = renamed_slice.dropna(subset=['date']).copy()

    price_cols = ['mar', 'may', 'jul', 'sep', 'dec', 'nearby']
    load_future_filtered[price_cols] = load_future_filtered[price_cols].apply(pd.to_numeric, errors = 'coerce')

    load_future_filtered[['iso_year', 'iso_week']] = load_future_filtered['date'].dt.isocalendar()[['year', 'week']].astype(int)
    expected_start = pd.Timestamp('1989-11-03')

    assert load_future_filtered['date'].min() == expected_start, f"Expected start date {expected_start}, but got {load_future_filtered['date'].min()}"
    assert (load_future_filtered['date'].dt.dayofweek == 4).all(), "Data quality error: Not all dates are Fridays."
    assert load_future_filtered['nearby'].count() == 1923

    load_future_filtered = load_future_filtered.reset_index(drop = True)

    return load_future_filtered

def load_merged(cash_path, futures_path):
    cash = load_cash(cash_path)
    futures = load_futures(futures_path)
    merged = cash.merge(futures, on=["iso_year", "iso_week"],
            how="inner", validate="one_to_one")
    merged = merged.rename(columns={"date_x": "cash_date", "date_y": "futures_date"})
    assert (merged["futures_date"] - merged["cash_date"]).dt.days.isin([1]).all()
    assert len(merged) == 1925, f"Expected 1925 merged rows, got {len(merged)}"
    return merged

