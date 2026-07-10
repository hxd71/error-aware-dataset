import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np

def direct_solution():
    """
    Main function to:
    1) Draw a choropleth map of COVID-19 death rate (deaths/cases) by contiguous US counties,
       using data from 2020-12-31, quantile classification, Conus Albers projection, size 15x10 inches.
    2) Draw a scatter plot of death rate vs senior resident rate (percentage of population 65+),
       with linear regression line, R² and p-value, point transparency 50%, red line, size 15x10 inches.
    
    Input data files (paths are predefined):
        - COVID-19 CSV: us-counties-2020.csv (daily accumulated cases/deaths)
        - County boundaries shapefile: contiguous_counties.zip (EPSG:4269, GEOID for FIPS)
        - Census ACS2020 data: ACS2020_5year_county.csv (population by age groups)
    Output:
        - choropleth map displayed and saved as 'choropleth_death_rate.png'
        - scatter plot displayed and saved as 'scatter_death_rate_vs_senior.png'
    """
    # File paths
    covid_csv = r"<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\covid_death_rate\us-counties-2020.csv"
    county_shp = r"<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\covid_death_rate\contiguous_counties.zip"
    census_csv = r"<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\covid_death_rate\ACS2020_5year_county.csv"

    # ------------------------------------------------------------------
    # 1. COVID-19 data: filter for 2020-12-31, compute death rate
    # ------------------------------------------------------------------
    covid_df = pd.read_csv(covid_csv, dtype={'fips': str})
    covid_df = covid_df[covid_df['date'] == '2020-12-31']
    covid_df = covid_df.dropna(subset=['fips', 'cases', 'deaths'])
    covid_df['fips'] = covid_df['fips'].str.zfill(5)          # ensure 5‑digit FIPS
    covid_df = covid_df[covid_df['cases'] > 0]                # avoid division by zero
    covid_df['death_rate'] = covid_df['deaths'] / covid_df['cases']
    covid_df = covid_df[['fips', 'death_rate']].copy()

    # ------------------------------------------------------------------
    # 2. County boundaries: load, project to Albers Equal Area (conus)
    # ------------------------------------------------------------------
    counties_gdf = gpd.read_file(county_shp)                   # shapefile in a ZIP
    # Original CRS is EPSG:4269 (NAD83 geographic)
    # Albers Equal Area for contiguous US (ESRI:102003)
    conus_albers = ("+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 "
                    "+lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m")
    counties_gdf = counties_gdf.to_crs(conus_albers)
    counties_gdf['GEOID'] = counties_gdf['GEOID'].astype(str).str.zfill(5)

    # ------------------------------------------------------------------
    # 3. Merge COVID death rates with county geometries
    # ------------------------------------------------------------------
    merged_gdf = counties_gdf.merge(covid_df, left_on='GEOID', right_on='fips', how='inner')

    # ------------------------------------------------------------------
    # 4. Choropleth map (death rate, quantiles)
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(15, 10))
    merged_gdf.plot(
        column='death_rate',
        scheme='quantiles',
        k=5,
        legend=True,
        legend_kwds={'title': "Death Rate (deaths per case)"},
        ax=ax,
        edgecolor='grey',
        linewidth=0.1
    )
    ax.set_title("COVID-19 Death Rate by County (2020-12-31) – Contiguous US")
    ax.axis('off')
    plt.tight_layout()
    plt.savefig("choropleth_death_rate.png")
    plt.show()

    # ------------------------------------------------------------------
    # 5. Census data: load required columns, clean, compute senior rate
    # ------------------------------------------------------------------
    census_cols = [
        'FIPS', 'Total Population',
        'Total Population: 65 to 74 Years',
        'Total Population: 75 to 84 Years',
        'Total Population: 85 Years and Over'
    ]
    census_df = pd.read_csv(census_csv, dtype={'FIPS': str}, usecols=census_cols)
    census_df = census_df.dropna(subset=census_cols[1:])      # drop if any population column is NaN
    census_df['FIPS'] = census_df['FIPS'].str.zfill(5)

    # ------------------------------------------------------------------
    # 6. Merge census with the death‑rate GeoDataFrame (by FIPS)
    # ------------------------------------------------------------------
    analysis_df = merged_gdf.merge(census_df, left_on='GEOID', right_on='FIPS', how='inner')
    # Sum senior population
    senior_cols = census_cols[2:]   # the three 65+ columns
    analysis_df['senior_pop'] = analysis_df[senior_cols].sum(axis=1)
    analysis_df['senior_rate'] = (
        analysis_df['senior_pop'] / analysis_df['Total Population']
    ) * 100    # percentage
    analysis_df = analysis_df.dropna(subset=['death_rate', 'senior_rate'])

    # ------------------------------------------------------------------
    # 7. Scatter plot with regression line, R², p-value
    # ------------------------------------------------------------------
    x = analysis_df['senior_rate'].values
    y = analysis_df['death_rate'].values

    slope, intercept, r_value, p_value, _ = stats.linregress(x, y)
    r_squared = r_value ** 2

    fig2, ax2 = plt.subplots(figsize=(15, 10))
    ax2.scatter(x, y, alpha=0.5, label='County', color='steelblue')
    # Regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax2.plot(x_line, y_line, color='red', 
             label=f'Regression: $R^2={r_squared:.3f}$, $p={p_value:.3g}$')
    ax2.set_xlabel('Senior Resident Rate (%)')
    ax2.set_ylabel('Death Rate (deaths per case)')
    ax2.set_title('COVID-19 Death Rate vs Senior Resident Rate (County-level)')
    ax2.legend()
    plt.tight_layout()
    plt.savefig("scatter_death_rate_vs_senior.png")
    plt.show()

# Execute the function
direct_solution()