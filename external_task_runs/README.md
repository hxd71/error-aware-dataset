# External GIS Agent Task Runs

This folder stores non-GeoAgent task adapters and run records for building the
GIS error dataset from other open-source GIS agent papers in `GIS Agent.xlsx`.

## Source Repositories Checked

| Excel entry | Local path | Task/data status | Current decision |
| --- | --- | --- | --- |
| LLM-Geo / Autonomous GIS | `<LOCAL_REPO_ROOT>\LLM-Geo` | Has notebook case studies and local/URL data. | Primary runnable source. |
| LLM-Find | `<LOCAL_REPO_ROOT>\LLM-Find` | Has many retrieval cases, but many depend on external APIs/keys. | Candidate for later data-retrieval errors. |
| Change-Agent | `<LOCAL_REPO_ROOT>\Change-Agent` | Has code and token captions; image dataset/model weights are on HuggingFace. | Multimodal later, needs Qwen endpoint fixed. |
| CartoAgent | `<LOCAL_REPO_ROOT>\CartoAgent` | Has map style transfer code and small data. | Multimodal/cartographic later. |
| GeoReasoner | `<LOCAL_REPO_ROOT>\GeoReasoner` | Has code; stage 1 data on HuggingFace, street-view data restricted. | Not first batch. |
| GeoBenchX | `<LOCAL_REPO_ROOT>\GeoBenchX` | Has 202 benchmark tasks, 50 evaluator-tuning generated traces, and official data archive now downloaded under `external_task_runs/data/geobenchx`. | Strong source for audited tool-call GIS method errors. |
| MapReader | `<LOCAL_REPO_ROOT>\MapReader` | Full clone with sample historical map images and metadata; no LLM-agent task trace found yet. | Candidate only if a clear map-reading/georeference task can be audited. |

## LLM Configuration Used

Text GIS tasks use the DeepSeek OpenAI-compatible endpoint:

- Base URL: `https://api.deepseek.com/v1`
- Model observed from `/v1/models`: `deepseek-v4-pro`

The Qwen multimodal endpoint still fails during TLS handshake from this machine,
even with certificate verification disabled. Keep Qwen-only multimodal tasks
blocked until that endpoint is reachable.

## Runner

`llm_geo_runner.py` adapts LLM-Geo without modifying the upstream repository.
It injects the API key from an environment variable, deletes the temporary
`config.ini` after import, and forces Matplotlib to use a non-interactive
backend so runs do not block on `plt.show()`.

Example:

```powershell
$env:DEEPSEEK_API_KEY='<key>'
<PYTHON_ENV>\Scripts\python.exe external_task_runs\llm_geo_runner.py --task-id hospital_accessibility_sc --mode direct --model deepseek-v4-pro --debug-attempts 1 --data-mode local
```

## Data Materialized

| Task | Local data folder |
| --- | --- |
| `covid_death_rate` | `external_task_runs\data\llm_geo\covid_death_rate` |
| `hospital_accessibility_sc` | `external_task_runs\data\llm_geo\hospital_accessibility_sc` |
| `axis_order_sc_hospitals` | `external_task_runs\data\llm_geo\axis_order_sc_hospitals` |
| `population_equal_interval_nc` | `external_task_runs\data\llm_geo\population_equal_interval_nc` |
| `invalid_polygon_repair` | `external_task_runs\data\llm_geo\invalid_polygon_repair` |

## Runs Completed

| Run | Mode | Outcome | Notes |
| --- | --- | --- | --- |
| `20260709_131825_covid_death_rate_direct_deepseek-v4-pro` | direct | Executed without traceback, but produced no PNG/table artifacts. | Useful as an output-delivery/map persistence failure candidate. |
| `20260709_132150_hospital_accessibility_sc_direct_deepseek-v4-pro` | direct | Produced `sc_hospital_distance_map.png`. | Good positive/control run; CRS and km conversion look reasonable. |
| `20260709_132420_hospital_accessibility_sc_full_deepseek-v4-pro` | full | Framework marked completed, but final code fails with `NameError: zipcodes_gdf is not defined`. | Useful agent assembly/execution failure candidate. |
| `20260709_163054_axis_order_sc_hospitals_direct_deepseek-v4-pro` | direct | Framework marked completed, but manual re-execution fails with Shapely `TopologyException`. | Promoted to `C2. Invalid Geometry Handling`; evidence package created at `C_Spatial_Reasoning_Errors\C2_Invalid_Geometry_Handling\llm_geo_axis_order_sc_hospitals_c2`. |
| `20260709_163151_population_equal_interval_nc_direct_deepseek-v4-pro` | direct | Produced map and class-count CSV. | Promoted to `E1. Classification Scheme Misuse`; map uses 6 `UserDefined` classes although the task requires exactly 5 equal-interval classes. |
| `20260709_163312_invalid_polygon_repair_direct_deepseek-v4-pro` | direct | Produced repaired GeoJSON, CSV, and PNG. | Correct/control run; not promoted as an error sample. |

## Selection Audit

`runs\targeted_low_count_audit_20260709_1630.json` records the automated audit
for the three targeted low-count taxonomy tasks:

- `axis_order_sc_hospitals`: observed GIS error is C2, not the originally targeted A1.
- `population_equal_interval_nc`: observed E1 map classification error.
- `invalid_polygon_repair`: correct result, retained as a control run only.


## GeoNatureAgent / GeoBenchX Runs

`geonature_runner.py` adapts selected GeoNatureAgent Benchmark and GeoBenchX-style tasks using local JSON/GeoJSON data copied into `external_task_runs/data/geonature`.

Promoted GIS-error cases:

| Run | Outcome | Dataset sample |
| --- | --- | --- |
| `20260709_171038_gn_v5_62_forest_cover_rank_bigearthnet_deepseek-v4-pro` | Completed with all forest cover values incorrectly written as zero. | `B_Spatial_Data_Errors\B1_Dataset_Integrity_Violation\geonature_forest_cover_rank_bigearthnet_b1` |
| `20260709_171112_gn_v5_21_compare_co2_candidate_pool_deepseek-v4-pro` | Completed with zero candidate-pool values and an incorrect Equal decision. | `D_Spatial_Analysis_Errors\D3_Spatial_Statistical_Misinterpretation\geonature_co2_candidate_pool_d3` |
| `20260709_171537_gbx_port_murcia_50km_buffer_intersections_deepseek-v4-pro` | Failed on degenerate rings in the province GeoJSON before buffering. | `C_Spatial_Reasoning_Errors\C2_Invalid_Geometry_Handling\geobenchx_murcia_50km_buffer_c2` |

Excluded from the main GIS taxonomy:

- `gn_v5_31_habitat_beja_lulc`: schema/read failure; retained only as an auxiliary run.
- `gn_v5_44_andalucia_average_co2`: Windows UTF-8 decoding failure.
- `gn_v5_49_threshold_co2_high`: nested-schema lookup failure without a GIS result artifact.
- `gn_v5_50_dual_indicator_high_priority`: API chunked-encoding interruption.


## GeoBenchX Evaluator Tuning Trace Audits

The official GeoBenchX data archive (`Data.zip`, 484M) was downloaded and
extracted to `external_task_runs/data/geobenchx`. Two human-scored generated
tool-call traces from `benchmark_set/evaluator_tuning_set.json` were
materialized and audited against local data.

Promoted GIS-error cases:

| Run | Outcome | Dataset sample |
| --- | --- | --- |
| `20260709_geobenchx_task_367674_earthquake_population_heatmap` | Generated workflow mapped earthquake magnitude and skipped raster-to-point population extraction. | `D_Spatial_Analysis_Errors\D2_Spatial_Allocation_Error\geobenchx_earthquake_population_heatmap_d2` |
| `20260709_geobenchx_task_748943_rural_population_percentage` | Generated workflow mapped raw rural population counts while labeling them as percentages. | `D_Spatial_Analysis_Errors\D3_Spatial_Statistical_Misinterpretation\geobenchx_rural_population_percentage_d3` |

Excluded despite being present in GeoBenchX tuning data:

- one-year map year mismatches: weak or partial temporal selection errors, not typical GIS taxonomy cases.
- unsolvable-task rejection failures: useful for agent calibration but not GIS domain-result errors.
- regional-definition mismatches: often geographic knowledge ambiguity rather than spatial method failure.
