# Week 3: Simple fiber route planning

These instructions apply to the Week 3 routing exercise. Other course tasks retain their own scope.

## Inputs and scope

- Read `03_02_ggs662_agentic_application_route_planning.ipynb` before routing. Run the notebook preparation cells if settings have not been created.
- Reuse the files saved by 03_01: `route1_short.gpkg`, `roads.gpkg`, `power_lines.gpkg`, `rail_lines.gpkg`, and `settlements.gpkg`. Report missing files and identify the corresponding 03_01 save step. Do not download replacement data automatically.
- Preserve input files. Write a reproducible script and derived results under `outputs/week3_routing/`. Record the script's run command and package versions.
- Use the shortened baseline's exact endpoints, with the easterly endpoint as the start. Do not substitute Taveta or new city coordinates.
- Measure in EPSG:32737. Recreate the 03_01 rectangular study area using the saved margin (default 3,000 m). Use settlements only as map context.

## Shortest-path method

1. Inspect CRS, geometry types, missing/empty/invalid features, and coverage. Report excluded features. Keep valid line parts, explode multipart lines, clip to the study area, and remove duplicate geometry, including reversed copies.
2. Build separate undirected graphs for roads, power, and rail. Model potential fiber corridors, not vehicle travel. Split lines at within-layer intersections, then create an edge for each consecutive coordinate pair, retaining geometry, length in metres, and edge type. Skip zero-length edges. Handle closed lines as consecutive segments, not self-loops representing whole rings.
3. Use coordinate pairs as nodes with consistent precision. Any precision adjustment must be documented, small relative to the gap threshold, and must not silently bridge gaps. For this classroom model, assume 2D within-layer crossings connect. Explain that bridges, tunnels, and grade separation can invalidate this assumption. The exported road features are not a preserved OSM routing graph.
4. Count connected components before and after repairs. Do not discard all but the largest component. Find nearest points between different components and add the smallest eligible straight connector, splitting touched edges at those points. Recompute components and repeat until no eligible component gaps remain. Use spatial indexing to narrow candidate pairs when needed.
5. A gap connector must be no longer than `gap_tolerance_m` (default 50 m) and fully covered by the study area. Retain its geometry and label `gap_connector`. Never silently move source lines, bridge larger gaps, or increase tolerances to force success.
6. Attach each fixed endpoint to its nearest point on the repaired network, splitting the touched edge. Include a straight `endpoint_connector` only within `endpoint_connector_limit_m` (default 500 m) and fully inside the study area. An endpoint already on a line needs a node, not a zero-length connector. If attachment exceeds the limit, mark that candidate `endpoint_too_far`.
7. Run `networkx.shortest_path` with `weight="length_m"` and `method="dijkstra"`. Use a simple graph retaining the shortest edge for duplicate node pairs, or explicitly select and retain edge keys if using a multigraph. Store connector types so they can be audited.
8. If the attached endpoints remain disconnected, report `no_path`. If no usable lines remain, report `empty_network`. Never draw a direct substitute and call it a network route. Reconstruct successful routes from ordered, correctly oriented edge geometries.

## Simple costs

- Compare `baseline`, `roads`, `power`, and `rail`, using one common positive rate from the settings (default USD 10/m). This is an invented classroom value, not a sourced construction estimate.
- Calculate `estimated_cost_usd = length_m * cost_per_m_usd`. Include all used gap and endpoint connector lengths exactly once in total route length. Round only displayed results.
- Record length, length in km, connector total length, connector count, maximum connector length, rate, and total cost. Baseline connector values are zero. Unavailable candidates have blank lengths and costs, not zero costs.
- The shortest available route is cheapest under this uniform-rate model. Do not introduce corridor discounts, population scores, raster costs, or extra datasets for this exercise.

## Outputs and checks

- Save `routes.gpkg` (baseline and successful routes), `route_comparison.csv` (all four candidates), `route_map.png`, and `routing_report.md`. Save used connectors in `connectors.gpkg` with route and connector type. If no connectors are used, omit that file and explain why; remove any stale generated connector file from a previous run in this output folder.
- Use CSV columns `route`, `status`, `length_m`, `length_km`, `connector_m`, `connector_count`, `max_connector_m`, `cost_per_m_usd`, and `estimated_cost_usd`. Use status `ok` for successful routes.
- Verify endpoint agreement within 0.01 m, continuity, nonempty valid route geometry, and containment in the study area. Check reconstructed geometry length against the traversed-edge sum within 0.01 m. Check individual connector lengths against the appropriate thresholds, and verify the cost equation.
- Test the implementation on small synthetic examples: an already connected route, a gap below the threshold, a gap above it, an endpoint projected onto a line interior, and a disconnected candidate. Verify connector distance is counted once.
- Map inferred connectors distinctly and report component counts, exclusions, attachment distances, and failures. Keep OpenStreetMap attribution on maps.
- Treat inferred links as hypothetical construction. State the simplified crossing assumption and that mapped infrastructure does not establish access rights or construction feasibility.
- For sensitivity reruns, change only the requested setting and save to a separate subfolder. Preserve the first comparison.
