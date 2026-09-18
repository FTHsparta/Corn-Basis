import numpy as np
import pandas as pd

def load_cash(df_input):
    print("Reading excel file...")
    raw = pd.read_excel('data/raw/Grainpr_working (2).xlsx', sheet_name='CORN', header=None)
    my_slice = raw.iloc[8:, [0, 7, 17, 21]] #grabs the columns we want (date, kansas city, dodge city, garden city)

    renamed_slice = my_slice.rename(columns={0: 'date', 7: 'kansas_city', 17: 'dodge_city', 21: 'garden_city'}) #renames the columns for ease of use
    renamed_slice['date'] = pd.to_datetime(renamed_slice['date'], errors='coerce') #converts the date columns to datetime format and coercing errors

    load_cash_filtered = renamed_slice.dropna(subset=['date']).copy() #deletes the rows that return a null value for the previous line (the cells that aren't dates)

    #converts the remaining columns into numeric values
    load_cash_filtered['kansas_city'] = pd.to_numeric(load_cash_filtered['kansas_city'], errors='coerce')
    load_cash_filtered['dodge_city'] = pd.to_numeric(load_cash_filtered['dodge_city'], errors='coerce')
    load_cash_filtered['garden_city'] = pd.to_numeric(load_cash_filtered['garden_city'], errors='coerce')


    load_cash_filtered[['iso_year', 'iso_week']] = load_cash_filtered['date'].dt.isocalendar()[['year', 'week']] #adds iso year and week columns
    expected_start = pd.Timestamp('1988-01-07') #sets expected start date 

    #assertions (checks to make sure the numbers match the results I got by hand)
    assert load_cash_filtered['date'].min() == expected_start, f"Expected start date {expected_start}, but got {load_cash_filtered['date'].min()}" 
    assert (load_cash_filtered['date'].dt.dayofweek == 3).all(), "Data quality error: Not all dates are Thursdays."
    assert load_cash_filtered['kansas_city'].count() == 2015, "kansas city data amount does not match 2015"
    assert load_cash_filtered['dodge_city'].count() == 1906, "dodge city data amount does not match 1906"
    assert load_cash_filtered['garden_city'].count() == 1383, "garden city data amount does not match 1383"
    return load_cash_filtered

if __name__ == '__main__':
    cash = load_cash('data/raw/Grainpr.xlsx')
    print(cash.head())
    print(cash.tail())
    print(cash.isna().sum())

