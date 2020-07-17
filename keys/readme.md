# /Keys/
This houses the support files used as an interface they take the form:
Some are not included for privacy but they look like this:

selenium.yml:
```yaml
webdriver: path/to/chrome-driver
```

wunderground.yml:
```yaml

    url: https://www.wunderground.com/history/daily/--------/date/
    features:
      High Temp: high
      Low Temp: low
      Day Average Temp: temp_mean
      Precipitation (past 24 hours from 07:53:00): precip
      Dew Point: dew
      High: dew_high
      Low: dew_low
      Average: dew_mean
      Max Wind Speed: wind
      Visibility: vis
      Sea Level Pressure: pres
      Actual Time: day_len
    dates:
      start: 2020-07-01
      end: 2020-07-05
```
electric.yml:
```yaml
login url: -------
usage url: -------
dates:
  start: 2017-07-01
  end: 2019-06-30
```

