"""
Public API for weather utilities.

Provides a DutchWeather class that wraps KNMI retrieval and interpolation.
"""

import pandas as pd
from .knmi import fetch_hourly_dutch_weather_data
from .weather_interpolate import geo_interpolate_weather_data, temporal_interpolate_weather_data


class DutchWeather:
    """
    Utilities for retrieving and interpolating KNMI hourly weather data
    to arbitrary lat/lon locations in the Netherlands.
    """

    @staticmethod
    def get_interpolated_weather(start, end,
                                 lat__degN, lon__degE,
                                 interpolate__min=15,
                                 metrics=None):
        """
        Retrieve interpolated hourly weather data for a single location in the Netherlands.

        This function fetches KNMI hourly observations for the requested time interval,
        applies unit conversions and renaming according to the provided `metrics` mapping,
        and interpolates the station data to the specified latitude and longitude.

        Parameters
        ----------
        start : pandas.Timestamp
            Start of the desired time interval (tz-aware).
        end : pandas.Timestamp
            End of the desired time interval (tz-aware). Must be >= start.
        lat__degN : float
            Latitude of the target location in decimal degrees.
        lon__degE : float
            Longitude of the target location in decimal degrees.
        metrics : dict, optional
            Mapping of KNMI variable codes to output names and conversion factors.
            Each entry should be of the form:
                KNMI_code: (output_column_name, factor)
            Default metrics:
                - "T": ("temp_outdoor__degC", 0.1)
                    Hourly temperature at 1.5 m in 0.1°C units, converted to ˚C.
                - "FH": ("wind__m_s_1", 0.1)
                    Hourly mean wind speed in 0.1 m/s, converted to m/s.
                - "Q": ("sol_ghi__W_m_2", (100*100)/(60*60))
                    Global horizontal radiation in J/cm² per hour, converted to W/m².
                - "P": ("air_outdoor__Pa", 0.1*100)
                    Air pressure in 0.1 hPa, converted to Pa.
                - "U": ("air_outdoor_rel_humidity__0", 1/100)
                    Relative humidity in %, converted to fraction (0–1).
        interpolate__min : int, optional
            Target resolution (in minutes) for interpolation.

        Returns
        -------
        pandas.DataFrame
            Temporally and geospatially interpolated Dutch weather data for the target location.
            Indexed by a MultiIndex(timestamp, metric).

        Notes
        -----
        - The returned DataFrame does NOT include latitude/longitude of the target location.
        - Internally, station coordinates are used for geospatial interpolation.
        - The function automatically splits the KNMI data request into smaller chunks if the interval
          is long to avoid server-side limitations.
        """

        if metrics is None:
            metrics = {
                "T": ("temp_outdoor__degC", 0.1),           # Hourly temperature at 1.5 m in 0.1°C units, converted to ˚C.
                "FH": ("wind__m_s_1", 0.1),                 # Hourly mean wind speed in 0.1 m/s, converted to m/s.
                "Q": ("sol_ghi__W_m_2", (100*100)/(60*60)), # Global horizontal radiation in J/cm² per hour, converted to W/m².
                "P": ("air_outdoor__Pa", 0.1*100),          # Air pressure in 0.1 hPa, converted to Pa.
                "U": ("air_outdoor_rel_humidity__0", 1/100) # Relative humidity in %, converted to fraction (0–1).
            }

        # --- guard against invalid interval ---
        if end < start:
            raise ValueError(
                f"get_weather: end ({end}) must be >= start ({start})"
            )

        weather_interval = pd.Interval(left=start, right=end, closed="both")
        
        return (
            fetch_hourly_dutch_weather_data(weather_interval, metrics=metrics)
            .pipe(geo_interpolate_weather_data, lat__degN=lat__degN, lon__degE=lon__degE)
            .pipe(temporal_interpolate_weather_data, interpolate__min=interpolate__min)
        )
