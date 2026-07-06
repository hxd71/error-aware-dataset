from src.tools.vector_tools import filter_vector_by_attribute
import json

# Filter US counties to retain only contiguous US (exclude AK, HI, PR, and territories)
# Excluded STATEFP values:
#   '02' = Alaska
#   '15' = Hawaii
#   '72' = Puerto Rico
EXCLUDED_STATEFP_VALUES = ['02', '15', '72']

summary = filter_vector_by_attribute(
    input_vector=asset_paths_by_id["us_counties_data"],
    output_path=output_paths[0],
    field="STATEFP",
    operator="not_in",
    values=EXCLUDED_STATEFP_VALUES
)

print(json.dumps({
    "step_id": "step_01",
    "operation": "filter_vector_by_attribute",
    "filter_rule": f"STATEFP not_in {EXCLUDED_STATEFP_VALUES}",
    "source_path": asset_paths_by_id["us_counties_data"],
    "output_path": output_paths[0],
    "result": summary
}, indent=2))