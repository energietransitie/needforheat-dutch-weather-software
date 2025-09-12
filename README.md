# NeedForHeat Dutch weather software

This repository contains software to retrieve, process, and geospatially and temporally interpolate Dutch KNMI weather data.  

## Table of contents
- [Table of contents](#table-of-contents)
- [General info](#general-info)
- [Deploying](#deploying)
  - [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Developing](#developing)
  - [Prerequisites](#prerequisites-1)
  - [Contributing](#contributing)
- [Features](#features)
- [Status](#status)
- [License](#license)
- [Credits](#credits)

## General info
This software retrieves hourly KNMI weather data (temperature, wind speed, solar radiation, etc.), processes the raw files, and applies geospatial and temporal interpolation to provide weather time series for arbitrary locations in the Netherlands.  

The code builds on earlier developments in the Twomes, Brains4Buildings, and REDUCEDHEATCARB projects.  
It is designed for integration with energy transition datasets such as [NeedForHeat](https://github.com/energietransitie/needforheat-dataset), but can also be used as a standalone tool.

## Deploying

### Prerequisites
* Python 3.9 or later
* `pip install -r requirements.txt`

Main dependencies:
* pandas
* numpy
* scipy
* requests
* tqdm

## Usage
Example: retrieve weather data for a single location and time span:

```python
from weather import DutchWeather
import pandas as pd

df_weather = DutchWeather.get_interpolated_weather(
    start=pd.Timestamp("2024-01-01 00:00:00", tz="Europe/Amsterdam"),
    end=pd.Timestamp("2024-01-02 00:00:00", tz="Europe/Amsterdam"),
    lat__degN=52.5012853331283,
    lon__degE=6.07953737762913,
    interpolate__min=5,
    metrics = {
        "T": ("temp_outdoor__degC", 0.1),           # Hourly temperature at 1.5 m in 0.1°C units, converted to ˚C.
        "FH": ("wind__m_s_1", 0.1),                 # Hourly mean wind speed in 0.1 m/s, converted to m/s.
        "Q": ("sol_ghi__W_m_2", (100*100)/(60*60)), # Global horizontal radiation in J/cm² per hour, converted to W/m².
        "P": ("air_outdoor__Pa", 0.1*100),          # Air pressure in 0.1 hPa, converted to Pa.
        "U": ("air_outdoor_rel_humidity__0", 1/100) # Relative humidity in %, converted to fraction (0–1).
    }

)

df_weather_props = df_weather["value"].unstack("property")

temp_0_degC__K = 273.15
df_weather_props['temp_outdoor__K'] = df_weather_props['temp_outdoor__degC'] + temp_0_degC__K

print(df_weather_props.head(25))
```
This prints the first 25 rows of a pandas DataFrame with interpolated weather parameters.

When using [Grasshopper](https://www.grasshopper3d.com/) in combination with Python 3, you can use

```python
# venv: ewf-tech
# requirements: numpy==1.26.4, scipy==1.13.1, pandas==2.2.2, pytz==2025.2, git+https://github.com/energietransitie/needforheat-dutch-weather-software.git
from weather import DutchWeather
import pandas as pd
df_weather = DutchWeather.get_interpolated_weather(
    start=pd.Timestamp("2024-01-01 00:00:00", tz="Europe/Amsterdam"),
    end=pd.Timestamp("2024-01-02 00:00:00", tz="Europe/Amsterdam"),
    lat__degN=52.5012853331283,
    lon__degE=6.07953737762913,
    interpolate__min=5,
    metrics = {
        "T": ("temp_outdoor__degC", 0.1),           # Hourly temperature at 1.5 m in 0.1°C units, converted to ˚C.
        "FH": ("wind__m_s_1", 0.1),                 # Hourly mean wind speed in 0.1 m/s, converted to m/s.
        "Q": ("sol_ghi__W_m_2", (100*100)/(60*60)), # Global horizontal radiation in J/cm² per hour, converted to W/m².
        "P": ("air_outdoor__Pa", 0.1*100),          # Air pressure in 0.1 hPa, converted to Pa.
        "U": ("air_outdoor_rel_humidity__0", 1/100) # Relative humidity in %, converted to fraction (0–1).
    }
)

df_weather_props = df_weather["value"].unstack("property")

temp_0_degC__K = 273.15
df_weather_props['temp_outdoor__K'] = df_weather_props['temp_outdoor__degC'] + temp_0_degC__K

# For Grasshopper: output dataframe on default port a
a = df_weather_props
```

## Developing

### Prerequisites

- Python 3.9 or later
- Recommended: a virtual environment

```
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```
### Contributing
Fork the repository, make changes in a feature branch, and submit a pull request.  
Please follow PEP8 style guidelines and include tests where relevant.

## Features

Ready:
* Retrieve raw hourly KNMI weather data
* Parse and process KNMI station metadata
* Geospatial interpolation to arbitrary lat/lon in the Netherlands
* Temporal interpolation
* Convenience function for single-location queries

To-do:
* Batch queries for multiple locations / timespans
* API key support for KNMI API v3
* Caching of downloaded weather files

## Status
Project is: _in progress_  
A minimal working version is available, with further extensions planned.

## License
This software is available under the [Apache 2.0 license](./LICENSE), Copyright 2025 [Research Group Energy Transition, Windesheim University of Applied Sciences](https://windesheim.nl/energietransitie)

## Credits
This software was written by:
* Henri ter Hofte · [@henriterhofte](https://github.com/henriterhofte)

It was inspired by:
* [needforheat-diagnosis-software](https://github.com/energietransitie/needforheat-diagnosis-software), by [@henriterhofte](https://github.com/henriterhofte) and contributors, licensed under [Apache 2.0](https://opensource.org/licenses/Apache-2.0)
* [HourlyHistoricWeather](https://github.com/stephanpcpeters/HourlyHistoricWeather), by [@stephanpcpeters](https://github.com/stephanpcpeters), licensed under [an MIT-style licence](https://raw.githubusercontent.com/stephanpcpeters/HourlyHistoricWeather/master/historicdutchweather/LICENSE)
  
We use and gratefully acknowledge the efforts of the makers of the following source code and libraries:
* [pandas](https://pandas.pydata.org/), by the Pandas development team, licensed under [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* [numpy](https://numpy.org/), by the NumPy development team, licensed under [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* [scipy](https://scipy.org/), by the SciPy community, licensed under [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* [requests](https://docs.python-requests.org/), by Kenneth Reitz and contributors, licensed under [Apache 2.0](https://opensource.org/licenses/Apache-2.0)
* [tqdm](https://tqdm.github.io/), by Noam Yorav-Raphael et al., licensed under [MPL-2.0](https://opensource.org/licenses/MPL-2.0)
