import io
import re
import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import timedelta
from scipy.interpolate import RBFInterpolator


class DutchWeather:
    """
    Utilities for retrieving and interpolating KNMI hourly weather data
    to arbitrary lat/lon locations in the Netherlands.
    """

    KNMI_API_URL = "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"

    @staticmethod
    def download_knmi_uurgegevens(start__YYYYMMDD, end__YYYYMMDD, metrics):
        """Download raw hourly KNMI data as text."""
        params = {
            "start": start__YYYYMMDD + "01",
            "end": end__YYYYMMDD + "24",
            "vars": ":".join(metrics),
        }
        response = requests.get(DutchWeather.KNMI_API_URL, params=params)
        response.raise_for_status()
        return response.text

    @staticmethod
    def process_knmi_weather_data(raw_data):
        """Convert KNMI raw text into a clean DataFrame indexed by (lat, lon, timestamp)."""
        lines = raw_data.splitlines()[5:]

        # Station info lines
        station_lines = [lines[0].lstrip("# ")]
        header_found = False
        data_start_line = 0

        for i, line in enumerate(lines):
            if re.match(r"^# \d{3}", line):
                station_lines.append(line.lstrip("# "))
            elif line.startswith("# STN,YYYYMMDD"):
                header_found = True
            elif header_found:
                data_start_line = i
                break

        df_stations = pd.read_fwf(io.StringIO("\n".join(station_lines)))
        df_stations.columns = df_stations.columns.str.replace(r"\(.*\)", "", regex=True).str.strip()
        df_stations = df_stations.set_index("STN")

        if not header_found:
            return pd.DataFrame()

        df_weather = pd.read_csv(io.StringIO(raw_data), skiprows=data_start_line + 4, delimiter=",")
        df_weather.columns = [col.replace("#", "").strip() for col in df_weather.columns]

        # Construct timestamp
        df_weather["timestamp"] = pd.to_datetime(
            df_weather["YYYYMMDD"].astype(str)
            + df_weather["HH"].astype(int).sub(1).astype(str).str.zfill(2),
            format="%Y%m%d%H",
        ).dt.tz_localize("UTC")

        df_weather.drop(columns=["YYYYMMDD", "HH"], inplace=True)
        df_weather = df_weather.dropna(subset=["timestamp"])
        df_weather = df_weather.set_index(["STN", "timestamp"])

        # Add station coordinates
        df_weather = df_weather.merge(df_stations[["LON", "LAT"]], left_on="STN", right_index=True, how="left")
        df_weather = df_weather.reset_index().drop(columns=["STN"])
        df_weather = df_weather.rename(columns={"LAT": "lat__degN", "LON": "lon__degE"})
        df_weather = df_weather.set_index(["lat__degN", "lon__degE", "timestamp"]).sort_index()

        return df_weather.dropna()

    @staticmethod
    def fetch_weather_data(time_interval, metrics):
        """Fetch and process weather data into a single DataFrame."""
        df_weather = pd.DataFrame()

        target__tz = time_interval.left.tzinfo
        start_date = time_interval.left.tz_convert("UTC").normalize()
        end_date = time_interval.right.tz_convert("UTC").normalize() + pd.Timedelta(days=1)

        for current_start in tqdm(pd.date_range(start=start_date, end=end_date, freq="4W")):
            current_end = min(end_date, current_start + pd.Timedelta("4W") - timedelta(seconds=1))
            raw_data = DutchWeather.download_knmi_uurgegevens(
                current_start.strftime("%Y%m%d"),
                current_end.strftime("%Y%m%d"),
                metrics.keys(),
            )
            df_chunk = DutchWeather.process_knmi_weather_data(raw_data)
            if df_chunk.empty:
                continue

            df_chunk = df_chunk.apply(pd.to_numeric, errors="coerce")

            # Apply metric renaming and conversion
            for metric, (new_name, factor) in metrics.items():
                if metric in df_chunk.columns:
                    df_chunk[new_name] = df_chunk[metric] * factor
                    df_chunk = df_chunk.drop(columns=[metric])

            df_weather = pd.concat([df_weather, df_chunk])

        if not df_weather.empty:
            df_weather = df_weather.reset_index().dropna().drop_duplicates()
            if target__tz is not None:
                df_weather["timestamp"] = df_weather["timestamp"].dt.tz_convert(target__tz)
            df_weather = df_weather.set_index(["timestamp", "lat__degN", "lon__degE"]).sort_index()

        return df_weather

    @staticmethod
    def interpolate_weather_data(df_weather, lat, lon):
        """Interpolate weather data to a single location (lat, lon)."""
        results = []

        df_weather = df_weather.reorder_levels(["timestamp", "lat__degN", "lon__degE"]).sort_index()

        for timestamp in df_weather.index.get_level_values("timestamp").unique():
            df_timestamp = df_weather.xs(timestamp, level="timestamp")
            lat_lon_array = df_timestamp.index.to_numpy()
            for metric in df_timestamp.columns:
                interpolator = RBFInterpolator(lat_lon_array, df_timestamp[metric].values)
                value = float(interpolator(np.array([[lat, lon]])).astype("float32"))
                results.append({"timestamp": timestamp, "property": metric, "value": value})

        df_out = pd.DataFrame(results).set_index(["timestamp", "property"]).sort_index()
        return df_out

    @staticmethod
    def get_weather(lat, lon, start, end):
        """
        Main convenience function: retrieve interpolated weather for one location.

        Parameters:
        - lat, lon: coordinates in degrees
        - start, end: tz-aware pandas Timestamps
        """
        metrics = {
            "T": ("temp_outdoor__degC", 0.1),
            "FH": ("wind__m_s_1", 0.1),
            "Q": ("sol_ghi__W_m_2", (100 * 100) / (60 * 60)),
            "P": ("air_outdoor__Pa", 0.1 * 100),
            "U": ("air_outdoor_rel_humidity__0", 1 / 100),
        }
        weather_interval = pd.Interval(left=start, right=end, closed="both")
        df_weather = DutchWeather.fetch_weather_data(weather_interval, metrics)
        return DutchWeather.interpolate_weather_data(df_weather, lat, lon)
