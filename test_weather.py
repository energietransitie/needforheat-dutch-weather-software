from weather import DutchWeather
import pandas as pd

start = pd.Timestamp("2024-01-01 00:00:00", tz="Europe/Amsterdam")
end   = pd.Timestamp("2024-08-01 00:00:00", tz="Europe/Amsterdam")

df = DutchWeather.get_weather(
    lat__degN=52.140,
    lon__degE=6.200,
    start=start,
    end=end
)

print(df.head(25))
