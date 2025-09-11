import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator
from tqdm.auto import tqdm

def interpolate_weather_data(
    df_weather: pd.DataFrame,
    lat__degN: float,
    lon__degE: float
) -> pd.DataFrame:
    """
    Interpolate weather data from stations to a single target location.

    Parameters
    ----------
    df_weather : pd.DataFrame
        MultiIndex (timestamp, lat__degN, lon__degE] + weather metrics.
    lat__degN, lon__degE : float
        Target coordinates for interpolation.

    Returns
    -------
    pd.DataFrame
        MultiIndex: (timestamp, metric)
        Columns: geospatially interpolated weather metrics for lat__degN, lon__degE 
    """

    # Prepare the output DataFrame
    interpolated_data = []

    df_weather = df_weather.reorder_levels(['timestamp', 'lat__degN', 'lon__degE']).sort_index()
    
    
    # Iterate over each timestamp
    for timestamp in tqdm(df_weather.index.get_level_values('timestamp').unique(), desc="Interpolating KNMI data geospatially"):
        df_timestamp = df_weather.xs(timestamp, level='timestamp')
        lat_lon = df_timestamp.index.values
        lat_lon_array = np.array([[lat__degN, lon__degE] for lat__degN, lon__degE in lat_lon])
        
        for metric in df_timestamp.columns:
            values = df_timestamp[metric].values
    
            # Set up the interpolator
            interpolator = RBFInterpolator(lat_lon_array, values)
    
            # Create an array of the weather location coordinates
            weather_coords = np.array([[lat__degN, lon__degE]])

            interpolated_value = interpolator(weather_coords)

            # Convert the interpolated value to Float32
            interpolated_value = float(interpolated_value.astype('float32'))
            
            # Append the interpolated value to the results list
            interpolated_data.append({
                'timestamp': timestamp,
                'property': metric,
                'value': interpolated_value
            })
    
    # Convert the results list to a DataFrame
    df_meas_weather = pd.DataFrame(interpolated_data)

    # Convert relevant columns to categorical type
    df_meas_weather['property'] = df_meas_weather['property'].astype('category')

    # Set the appropriate multi-index
    df_meas_weather.set_index(['timestamp', 'property'], inplace=True)
    
    return df_meas_weather 