from policyengine_us import Microsimulation
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

sim = Microsimulation(dataset = "hf://policyengine/test/sparse_cd_stacked_2023.h5")

# Quick fix for state ids that don't match (NOTE: these are resampled, reweighted households)
cd_geoids = sim.calculate("congressional_district_geoid").values
correct_state_fips = cd_geoids // 100
sim.set_input("state_fips", 2023, correct_state_fips)

# Get an analysis dataframe
df = sim.calculate_dataframe(['household_id', 'state_fips', 'congressional_district_geoid', 'income_tax', 'household_weight'])

# Load the hexagon shapefile
hex_gdf = gpd.read_file('HexCDv31/HexCDv31.shp')
hex_gdf['cd_id'] = hex_gdf['GEOID'].astype(int)

# Aggregate income tax by congressional district (weighted average)
district_stats = df.groupby('congressional_district_geoid').apply(
    lambda x: pd.Series({
        'total_income_tax': (x['income_tax'] * x['household_weight']).sum(),
        'total_households': x['household_weight'].sum(),
        'avg_income_tax': (x['income_tax'] * x['household_weight']).sum() / x['household_weight'].sum()
    })
).reset_index()

# Merge data with shapefile
merged_gdf = hex_gdf.merge(
    district_stats, 
    left_on='cd_id', 
    right_on='congressional_district_geoid',
    how='left'
)

# Create the visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Plot 1: Total Income Tax
merged_gdf.plot(
    column='total_income_tax',
    ax=ax1,
    legend=True,
    cmap='RdYlGn_r',
    edgecolor='black',
    linewidth=0.3,
    missing_kwds={'color': 'lightgray', 'label': 'No Data'}
)
ax1.set_title('Total Income Tax by Congressional District', fontsize=14, fontweight='bold')
ax1.axis('off')

# Plot 2: Average Income Tax per Household
merged_gdf.plot(
    column='avg_income_tax',
    ax=ax2,
    legend=True,
    cmap='viridis',
    edgecolor='black',
    linewidth=0.3,
    missing_kwds={'color': 'lightgray', 'label': 'No Data'}
)
ax2.set_title('Average Income Tax per Household by Congressional District', fontsize=14, fontweight='bold')
ax2.axis('off')

plt.suptitle('Income Tax Analysis by Congressional District (2023)', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('income_tax_by_district.png', dpi=300, bbox_inches='tight')
plt.show()

# Print summary statistics
print("\n=== Summary Statistics ===")
print(f"Districts with data: {district_stats.shape[0]}")
print(f"Total districts in shapefile: {hex_gdf.shape[0]}")
print(f"\nTop 5 Districts by Total Income Tax:")
top_5 = district_stats.nlargest(5, 'total_income_tax')[['congressional_district_geoid', 'total_income_tax', 'avg_income_tax']]
top_5['total_income_tax'] = top_5['total_income_tax'].apply(lambda x: f"${x:,.0f}")
top_5['avg_income_tax'] = top_5['avg_income_tax'].apply(lambda x: f"${x:,.0f}")
print(top_5.to_string(index=False))

print(f"\nBottom 5 Districts by Total Income Tax:")
bottom_5 = district_stats.nsmallest(5, 'total_income_tax')[['congressional_district_geoid', 'total_income_tax', 'avg_income_tax']]
bottom_5['total_income_tax'] = bottom_5['total_income_tax'].apply(lambda x: f"${x:,.0f}")
bottom_5['avg_income_tax'] = bottom_5['avg_income_tax'].apply(lambda x: f"${x:,.0f}")
print(bottom_5.to_string(index=False))
