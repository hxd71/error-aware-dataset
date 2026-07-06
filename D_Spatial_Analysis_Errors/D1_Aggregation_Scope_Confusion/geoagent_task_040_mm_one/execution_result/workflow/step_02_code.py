from src.tools.report_tools import export_vector_table
import json

# Export county fast food counts to CSV with only required columns
summary = export_vector_table(
    artifact_paths_by_name["pa_county_fastfood_counts.geojson"],
    output_path=output_paths[0],
    columns=["NAME", "fastfood_count"]
)

print(json.dumps({
    "step_id": "step_02",
    "operation": "export_vector_table",
    "input": "pa_county_fastfood_counts.geojson",
    "output": "pa_fastfood_by_county.csv",
    "columns_exported": ["NAME", "fastfood_count"],
    "summary": summary
}))