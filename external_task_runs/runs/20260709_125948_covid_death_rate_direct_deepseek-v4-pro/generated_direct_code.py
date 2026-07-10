import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def direct_solution():
    """
    Generate a choropleth map of COVID-19 death rate (deaths/cases) for contiguous US counties
    (data from 2020-12-31) and a scatter plot showing the correlation with senior resident rate,
    including regression line, R², and p-value.
    """
    # -------------------------------
    # 1. Load COVID-19 daily county data
    covid_url = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties-2020.csv"
    covid_df = pd.read_csv(covid_url, dtype={'fips': str})  # read FIPS as string
    # Keep only the last day of 2020 (2020-12-31)
    covid_dec31 = covid_df[covid_df['date'] == '2020-12-31'].copy()
    # Remove rows with missing FIPS, cases or deaths
    covid_dec31 = covid_dec31.dropna(subset=['fips', 'cases', 'deaths'])
    # Ensure 5-digit county FIPS with leading zeros
    covid_dec31['fips'] = covid_dec31['fips'].str.zfill(5)
    # Compute death rate (deaths / cases); protect against division by zero
    covid_dec31['death_rate'] = covid_dec31['deaths'] / covid_dec31['cases']
    covid_dec31.replace([np.inf, -np.inf], np.nan, inplace=True)
    covid_dec31 = covid_dec31.dropna(subset=['death_rate'])
    # Each row now contains: fips, cases, deaths, death_rate

    # -------------------------------
    # 2. Load ACS 2020 census data
    census_url = "https://raw.githubusercontent.com/gladcolor/spatial_data/master/Demography/ACS2020_5year_county.csv"
    census_df = pd.read_csv(census_url, dtype={'FIPS': str})
    cols_needed = [
        'FIPS',
        'Total Population',
        'Total Population: 65 to 74 Years',
        'Total Population: 75 to 84 Years',
        'Total Population: 85 Years and Over'
    ]
    census_df = census_df[cols_needed].copy()
    # Drop rows with any missing values in these columns
    census_df = census_df.dropna()
    # Ensure 5-digit FIPS with leading zeros
    census_df['FIPS'] = census_df['FIPS'].str.zfill(5)
    # Compute senior population (65+)
    senior_cols = [
        'Total Population: 65 to 74 Years',
        'Total Population: 75 to 84 Years',
        'Total Population: 85 Years and Over'
    ]
    census_df['senior_pop'] = census_df[senior_cols].sum(axis=1)
    # Senior rate: fraction of population aged 65+; ignore zero-population rows
    census_df = census_df[census_df['Total Population'] > 0]
    census_df['senior_rate'] = census_df['senior_pop'] / census_df['Total Population']

    # -------------------------------
    # 3. Merge COVID and census data on FIPS
    merged_df = pd.merge(
        covid_dec31,
        census_df[['FIPS', 'senior_rate']],
        left_on='fips',
        right_on='FIPS',
        how='inner'
    )
    # merged_df now contains fips, death_rate, senior_rate (plus other columns)

    # -------------------------------
    # 4. Load contiguous US county boundaries
    counties_url = "https://github.com/gladcolor/spatial_data/raw/master/contiguous_counties.zip"
    counties_gdf = gpd.read_file(counties_url)
    # Ensure GEOID column is a 5-digit string with leading zeros
    counties_gdf['GEOID'] = counties_gdf['GEOID'].astype(str).str.zfill(5)
    # Project to Conus Albers Equal Area (EPSG:5070)
    counties_proj = counties_gdf.to_crs("EPSG:5070")

    # -------------------------------
    # 5. Merge county geometries with the combined COVID+census data
    map_gdf = counties_proj.merge(
        merged_df,
        left_on='GEOID',
        right_on='fips',
        how='inner'
    )
    # map_gdf is a GeoDataFrame with geometry and death_rate column

    # -------------------------------
    # 6. Choropleth map of death rate
    fig1, ax1 = plt.subplots(1, 1, figsize=(15, 10))
    map_gdf.plot(
        column='death_rate',
        scheme='quantiles',
        k=5,
        legend=True,
        ax=ax1,
        legend_kwds={'title': 'Death Rate (Deaths/Cases)'},
        cmap='OrRd',
        edgecolor='0.8',
        linewidth=0.1
    )
    ax1.set_title('COVID-19 Death Rate (Deaths/Cases) – 2020-12-31', fontsize=16)
    ax1.set_axis_off()

    # -------------------------------
    # 7. Scatter plot: death rate vs senior rate with regression
    scatter_df = merged_df[['senior_rate', 'death_rate']].dropna()
    x = scatter_df['senior_rate']
    y = scatter_df['death_rate']

    slope, intercept, r_value, p_value, _ = stats.linregress(x, y)
    r_squared = r_value ** 2
    line = slope * x + intercept

    fig2, ax2 = plt.subplots(figsize=(15, 10))
    ax2.scatter(x, y, alpha=0.5, c='blue', label='County')
    ax2.plot(x, line, color='red', label='Regression Line')
    ax2.text(
        0.05, 0.95,
        f'$R^2$ = {r_squared:.4f}\np = {p_value:.4e}',
        transform=ax2.transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)
    )
    ax2.set_xlabel('Senior Resident Rate (65+)')
    ax2.set_ylabel('Death Rate (Deaths/Cases)')
    ax2.set_title('Correlation between COVID-19 Death Rate and Senior Resident Rate')
    ax2.legend()

    # Display both figures
    plt.show()

# Execute the solution
direct_solution()