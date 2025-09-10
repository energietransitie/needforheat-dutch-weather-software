# NeedForHeat Dutch weather software

This repository contains software to retrieve, process, and geospatially interpolate Dutch KNMI weather data.  

## Table of contents
* [General info](#general-info)
* [Deploying](#deploying)
* [Developing](#developing)
* [Features](#features)
* [Status](#status)
* [License](#license)
* [Credits](#credits)

## General info
This software retrieves hourly KNMI weather data (temperature, wind speed, solar radiation, etc.), processes the raw files, and applies geospatial interpolation to provide weather time series for arbitrary locations in the Netherlands.  

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
from weather_extraction import get_weather_timeseries
import pandas as pd

start = pd.Timestamp("2024-01-01T00:00:00Z")
end   = pd.Timestamp("2024-01-07T23:00:00Z")

df = get_weather_timeseries(
    lat_degN=52.140,
    lon_degE=6.200,
    start=start,
    end=end
)
```
This returns a pandas DataFrame with interpolated weather parameters.

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
* Geospatial interpolation to arbitrary lat/lon
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
* [HourlyHistoricWeather](https://github.com/stephanpcpeters/HourlyHistoricWeather), by [@stephanpcpeters](https://github.com/stephanpcpeters), licensed under [an MIT-style licence](https://raw.githubusercontent.com/stephanpcpeters/HourlyHistoricWeather/master/historicdutchweather/LICENSE)
  
We use and gratefully acknowledge the efforts of the makers of the following source code and libraries:
* [pandas](https://pandas.pydata.org/), by the Pandas development team, licensed under [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* [numpy](https://numpy.org/), by the NumPy development team, licensed under [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* [scipy](https://scipy.org/), by the SciPy community, licensed under [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* [requests](https://docs.python-requests.org/), by Kenneth Reitz and contributors, licensed under [Apache 2.0](https://opensource.org/licenses/Apache-2.0)
* [tqdm](https://tqdm.github.io/), by Noam Yorav-Raphael et al., licensed under [MPL-2.0](https://opensource.org/licenses/MPL-2.0)
