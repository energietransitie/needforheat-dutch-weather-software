from weather import DutchWeather
import pandas as pd

df = DutchWeather.get_weather(
    start=pd.Timestamp("2024-01-01 00:00:00", tz="Europe/Amsterdam"),
    end=pd.Timestamp("2024-08-01 00:00:00", tz="Europe/Amsterdam"),
    lat__degN=52.5012853331283,
    lon__degE=6.07953737762913
)
 
print(df.head(25))
