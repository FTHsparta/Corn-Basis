# Kansas Corn Basis Forecasting

Research project for URES 200 at Kansas State University, mentored by Professor Brian Coffey. I'm testing how well simple moving-average forecasts predict weekly corn basis at three markets: Kansas City, Dodge City and Garden City.

## Data

Weekly corn cash prices and corn futures prices from the Livestock Marketing Information Center (LMIC), provided by Professor Coffey. The raw data files are not included in this repository.

- Sample: 1,131 weeks, 1/6/2005 to 9/3/2026
- Basis = cash price minus the nearby futures price, in cents per bushel
- Percentage basis = (cash - nearby) / nearby x 100
- 12 missing weekly cash prices are filled by linear interpolation and flagged

## Method

- The forecast for a week is the average basis in that same ISO week over the previous 3 years (or 4 years). Only past years are used, so there is no lookahead.
- Forecasts are made for 2009 onward, for both absolute basis and percentage basis.
- Week 53 only appears in some years, so it gets no forecast.
- Error = forecast - observed. I report mean error, mean absolute error (MAE) and root mean squared error (RMSE). Percentage errors are also converted to cents (pct error x nearby price) so they can be compared with absolute basis forecasts.

I'm currently working on adding a method that uses current basis information, following Taylor, Dhuyvetter & Kastens (2006).

## Code

- `src/load.py` loads the cash and futures data and merges them by ISO week
- `src/basis.py` calculates basis, sets the sample period and fills missing weeks
- `src/forecast.py` makes the 3- and 4-year forecasts, calculates errors and exports the results
- `src/plots.py` graphs prices, basis and Garden City forecast errors

Assertions in the code check results against values I calculated by hand in Excel.

To run, save the LMIC files as `data/raw/Grainpr.xlsx` and `data/raw/cornfutures.xlsx`, then from the repo root:

```
pip install -r requirements.txt
mkdir output
python src/forecast.py
```
