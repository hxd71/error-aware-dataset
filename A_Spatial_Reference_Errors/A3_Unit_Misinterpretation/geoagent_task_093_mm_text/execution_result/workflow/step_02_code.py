from src.tools.report_tools import export_vector_table

input_gpkg = artifact_paths_by_name["county_boundaries_km.gpkg"]
output_csv = output_paths[0]

summary = export_vector_table(
    input_vector=input_gpkg,
    output_path=output_csv,
    columns=["NAME", "boundary_km"],
    include_geometry=False
)

print(json.dumps({
    "step_id": "step_02",
    "status": "success",
    "output": output_csv,
    "features_exported": summary.get("features_written", 0)
}))