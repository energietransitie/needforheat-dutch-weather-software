from weather import DutchWeather
import pandas as pd

metrics = {
                "T": ("temp_outdoor__degC", 0.1),
                "FH": ("wind__m_s_1", 0.1),
                "Q": ("sol_ghi__W_m_2", (100*100)/(60*60)),
                "P": ("air_outdoor__Pa", 0.1*100),
                "U": ("humidity_outdoor_rel__0", 1/100)
            }

df_weather = DutchWeather.get_interpolated_weather(
    start=pd.Timestamp("2024-01-01 00:00:00", tz="Europe/Amsterdam"),
    end=pd.Timestamp("2024-01-02 00:00:00", tz="Europe/Amsterdam"),
    lat__degN=52.5012853331283,
    lon__degE=6.07953737762913,
    interpolate__min=5,
    metrics = metrics
)

df_weather_props = df_weather["value"].unstack("property")

temp_0_degC__K = 273.15
df_weather_props['temp_outdoor__K'] = df_weather_props['temp_outdoor__degC'] + temp_0_degC__K

print(df_weather_props.head(25))
