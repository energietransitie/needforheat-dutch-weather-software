import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator
from tqdm.auto import tqdm
import math


def geo_interpolate_weather_data(
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
    for timestamp in tqdm(df_weather.index.get_level_values('timestamp').unique(), desc="Geospatial interpolation..."):
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

def temporal_interpolate_weather_data(
        df_weather: pd.DataFrame,
        interpolate__min: int = 15) -> pd.DataFrame:
    """
    Temporal interpolation for weather/property data without gap handling.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with MultiIndex (timestamp, property) and a single 'value' column.
        Assumes:
          - No gaps in the timestamp sequence.
          - All values are floats.
    interpolate__min : int, optional
        Target resolution (in minutes) for interpolation.

    Returns
    -------
    pandas.DataFrame
        Interpolated DataFrame with the same MultiIndex (timestamp, property).
    """
    if not isinstance(df_weather.index, pd.MultiIndex):
        raise ValueError("Input DataFrame must have MultiIndex (timestamp, property).")
    if df_weather.index.names != ["timestamp", "property"]:
        raise ValueError("Expected MultiIndex with levels: ['timestamp', 'property'].")

    results = []

    # Process each property separately
    for prop, series in tqdm(df_weather.groupby(level="property")["value"], desc="Temporal interpolation..."):
        # Extract the timeseries for this property
        s = series.droplevel("property")

        # Compute modal interval (minutes)
        modal_intv__min = int(
            (s.index.to_series().diff().dropna().dt.total_seconds() / 60)
            .round()
            .mode()
            .iloc[0]
        )

        # Early exit: no interpolation needed
        if interpolate__min == modal_intv__min:
            s_interp = s.to_frame("value")
            s_interp["property"] = prop
            s_interp = s_interp.set_index("property", append=True)
            results.append(s_interp)
            continue

    # Otherwise, do the full pipeline
        # GCD to align modal interval with requested interpolate__min
        upsample__min = max(1, math.gcd(modal_intv__min, interpolate__min))

        # Resample → interpolate → resample
        s_interp = (
            s.resample(f"{upsample__min}min").first()
             .interpolate(method="time")
             .resample(f"{interpolate__min}min").mean()
        )

        # Reattach property index
        s_interp = s_interp.to_frame("value")
        s_interp["property"] = prop
        s_interp = s_interp.set_index("property", append=True)

        results.append(s_interp)

    return pd.concat(results).sort_index()