# weather_electric

brendan lafferty

## Tools:

#### weather_scaper.py
Used to scrape weather data from weather underground.
Settings for its use can be found in [keys/wunderground.yml](keys/wunderground.yml)
```bash
python weather_scraper.py
```

#### electric_scaper.py
Used to scrape my electric usage data and can be run from the command line:
```bash
python electric_scraper.py
```
it will prompt you as to what to do,  unfortunately for you it will not work as 
I have omitted the helper file for privacy see [keys/readme.md](keys/readme.md) for details


## Notebook:

#### data wrangling and modeling.py
This houses the data wrangling and the modeling process.  It generates all the output plots.