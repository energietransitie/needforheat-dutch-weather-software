"""
Public API for weather utilities.

Provides a DutchWeather class that wraps KNMI retrieval and interpolation.
"""

import pandas as pd
from .knmi import fetch_weather_data
from .geo_interpolate import interpolate_weather_data


class DutchWeather:
    """
    Utilities for retrieving and interpolating KNMI hourly weather data
    to arbitrary lat/lon locations in the Netherlands.
    """

    @staticmethod
    def get_weather(start, end, lat__degN, lon__degE):
        """
        Main convenience function: retrieve interpolated weather for one location.

        Parameters
        ----------
        lat__degN : float
            Latitude in decimal degrees.
        lon__degE : float
            Longitude in decimal degrees.
        start : pandas.Timestamp
            Start time (tz-aware).
        end : pandas.Timestamp
            End time (tz-aware).

        Returns
        -------
        pandas.DataFrame
            Indexed by timestamp, with weather metrics as columns.
        """
        metrics = {
            "T": ("temp_outdoor__degC", 0.1),
            "FH": ("wind__m_s_1", 0.1),
            "Q": ("sol_ghi__W_m_2", (100 * 100) / (60 * 60)),
            "P": ("air_outdoor__Pa", 0.1 * 100),
            "U": ("air_outdoor_rel_humidity__0", 1 / 100),
        }

        # --- guard against invalid interval ---
        if end < start:
            raise ValueError(
                f"get_weather: end ({end}) must be >= start ({start})"
            )

        weather_interval = pd.Interval(left=start, right=end, closed="both")
        df_weather = fetch_weather_data(weather_interval, metrics=metrics)
        return interpolate_weather_data(df_weather, lat__degN, lon__degE)
