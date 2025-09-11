import pandas as pd
import requests
import re
import io
from pandas.errors import ParserError
from tqdm.auto import tqdm
from datetime import timedelta

# KNMI hourly weather API (for Dutch stations)
KNMI_HOURLY_URL = "https://cdn.knmi.nl/knmi/map/page/klimatologie/uurgegevens/uurgeg_{year}.txt"


def download_knmi_uurgegevens(start__YYYYMMDD, end_YYYYMMDD, metrics=['T', 'FH', 'Q']):
    # KNMI API endpoint
    KNMI_API_URL = "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"
    
    # NB For a future version of these functions, you may also need an  API key for KNMI and put it in a file with the name below and one line KNMI_API_KEY=your_KNMI_API_key 
    knmi_api_keys_file='knmi_api_key.txt'
    # If your organistion does not have one yet, request one here: https://developer.dataplatform.knmi.nl/open-data-api#token
    base_url = KNMI_API_URL
    params = {
        'start': start__YYYYMMDD+'01',
        'end': end_YYYYMMDD+'24',
        'vars': ':'.join(metrics)
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from KNMI: {response.text}")
    return response.text

def process_knmi_weather_data(raw_data):
    # Split raw data by lines
    lines = raw_data.splitlines()

    # Ignore the first 5 lines
    lines = lines[5:]

    # Extract station info
    station_lines = [lines[0].lstrip('# ')]
    header_found = False
    data_start_line = 0


    for i, line in enumerate(lines):
        if re.match(r'^# \d{3}', line):
            station_lines.append(line.lstrip('# '))
        elif line.startswith('# YYYYMMDD'):
            continue
        elif line.startswith('# STN,YYYYMMDD'):
            header_found = True
        elif header_found:
            data_start_line = i
            break

    
    # Create station DataFrame
    station_data = "\n".join(station_lines)

    df_stations = pd.read_fwf(io.StringIO(station_data))
    df_stations.columns = df_stations.columns.str.replace(r'\(.*\)', '', regex=True).str.strip()
    df_stations = df_stations.set_index(['STN'])
    if (not header_found) & (data_start_line == 0):
        return pd.DataFrame() # Return an empty DataFrame
    else: 
        df_weather_chunk = pd.read_csv(io.StringIO(raw_data), skiprows=data_start_line+4, delimiter=',')    
    
        # Rename columns
        df_weather_chunk.columns = [col.replace('#', '').strip() for col in df_weather_chunk.columns]
        
        # Parse timestamp
        df_weather_chunk['timestamp'] = pd.to_datetime(df_weather_chunk['YYYYMMDD'].astype(str) + df_weather_chunk['HH'].astype(int).sub(1).astype(str).str.zfill(2), format='%Y%m%d%H')
        
        # Localize to UTC
        df_weather_chunk['timestamp'] = df_weather_chunk['timestamp'].dt.tz_localize('UTC')
    
        df_weather_chunk.drop(columns=['YYYYMMDD', 'HH'], inplace=True)
    
        # drop rows where timestamps are NaT (Not a Time)
        df_weather_chunk = df_weather_chunk.dropna(subset=['timestamp'])
    
        df_weather_chunk = df_weather_chunk.set_index(['STN', 'timestamp'])

        df_weather_chunk = df_weather_chunk.merge(df_stations[['LON', 'LAT']], left_on='STN', right_index=True, how='left')

        # Set the multi-index with lat, lon, and timestamp
        df_weather_chunk = df_weather_chunk.reset_index()

        # Drop the station identifier from the data
        df_weather_chunk = df_weather_chunk.drop(columns=['STN'])
        
        # Rename columns
        df_weather_chunk = df_weather_chunk.rename(columns={'LAT': 'lat__degN', 'LON': 'lon__degE'})
        df_weather_chunk = df_weather_chunk.set_index(['lat__degN', 'lon__degE', 'timestamp']).sort_index()

        # Drop rows with missing values 
        df_weather_chunk = df_weather_chunk.dropna()

        return df_weather_chunk


def fetch_weather_data(time_interval,
                       chunk_freq="4W", 
                       metrics=None):
    """
    Fetch and process weather data in chunks over a specified period.
    
    Parameters:
    time_interval (pd.Interval): Closed interval for the data collection period.
    chunk_freq (str): Frequency for dividing the data collection period into chunks.
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
                Air pressure in hPa, converted to Pa.
            - "U": ("air_outdoor_rel_humidity__0", 1/100)
                Relative humidity in %, converted to fraction (0–1).
    
    Returns:
    pd.DataFrame: Processed weather data with multi-index of latitude, longitude, and timestamp. The timezone of time_interval.left.tzinfo (if any) is used as the target timezone for the timestamps.
    """
    df_weather = pd.DataFrame()
    df_weather_chunk = pd.DataFrame()
    
    # # Ensure the start date is included in the first chunk
    # target__tz = time_interval.left.tzinfo
    # start_date = time_interval.left.tz_convert('UTC').normalize()
    # end_date = time_interval.right.tz_convert('UTC').normalize() + pd.Timedelta(days=1)
    # first_chunk_start = pd.date_range(start=start_date, end=end_date, freq=chunk_freq)[0]
    # first_chunk_start = first_chunk_start if start_date >= first_chunk_start else first_chunk_start - pd.Timedelta(chunk_freq)

    if metrics is None:
        metrics = {
            "T": ("temp_outdoor__degC", 0.1),
            "FH": ("wind__m_s_1", 0.1),
            "Q": ("sol_ghi__W_m_2", (100*100)/(60*60)),
            "P": ("air_outdoor__Pa", 0.1*100),
            "U": ("air_outdoor_rel_humidity__0", 1/100)
        }
    
    # Ensure the start date is included in the first chunk
    target__tz = time_interval.left.tzinfo

    if time_interval.right < time_interval.left:
        raise ValueError("fetch_weather_data: end must be >= start")

    start_date = time_interval.left.tz_convert("UTC").normalize()
    end_date = time_interval.right.tz_convert("UTC").normalize() + pd.Timedelta(days=1)

    chunk_starts = pd.date_range(start=start_date, end=end_date, freq=chunk_freq)

    # Fall back to start_date if the range is too short
    if len(chunk_starts) == 0:
        first_chunk_start = start_date
    else:
        first_chunk_start = chunk_starts[0]

    first_chunk_start = (
        first_chunk_start
        if start_date >= first_chunk_start
        else first_chunk_start - pd.Timedelta(chunk_freq)
    )

    # Iterate over date ranges using the specified frequency
    for current_start in tqdm(pd.date_range(start=first_chunk_start, end=end_date, freq=chunk_freq), desc="Downloading KNMI data"):
        current_end = min(end_date, current_start + pd.Timedelta(chunk_freq) - timedelta(seconds=1))
        current_start = max(start_date, current_start)

        raw_data = download_knmi_uurgegevens(current_start.strftime('%Y%m%d'),
                                                                    current_end.strftime('%Y%m%d'),
                                                                    metrics.keys()
                                                                )
        try:
            df_weather_chunk = process_knmi_weather_data(raw_data)
        except ParserError:
            print(f"ParserError on: {raw_data}")
            

        if df_weather_chunk.empty:
            print(f"No data found between {current_start} and {current_end} for {metrics.keys()}. Skipping to next iteration.")
            continue  # Move to the next iteration of the loop
            
        # Convert all columns to numeric, coercing errors to NaN
        df_weather_chunk = df_weather_chunk.apply(pd.to_numeric, errors='coerce')

        # Apply property renaming and conversion factors
        columns_to_drop = []
        for metric, (new_name, conversion_factor) in metrics.items():
            if metric in df_weather_chunk.columns:
                if conversion_factor is not None:
                    df_weather_chunk[new_name] = df_weather_chunk[metric] * conversion_factor
                else:
                    df_weather_chunk[new_name] = df_weather_chunk[metric
                    ]
            # Mark original column for dropping if the new name is different
            if new_name != metric:
                columns_to_drop.append(metric)
        
        # Remove original metric columns if they were renamed
        df_weather_chunk = df_weather_chunk.drop(columns=columns_to_drop)
    
        # Append chunk data to df_weather
        df_weather = pd.concat([df_weather, df_weather_chunk])

    if not df_weather_chunk.empty:
        
        # Cleanup and final formatting

        df_weather = df_weather.reset_index()
        df_weather = df_weather.dropna()
        df_weather = df_weather.drop_duplicates()
        
        # Convert the 'timestamp' column to the target timezone, if any
        if target__tz is not None:
            df_weather['timestamp'] = df_weather['timestamp'].dt.tz_convert(target__tz)

        df_weather = df_weather.set_index(['timestamp', 'lat__degN', 'lon__degE']).sort_index()

    return df_weather
