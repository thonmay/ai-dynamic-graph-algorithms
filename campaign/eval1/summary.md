# Campaign eval1

Medians over ended runs. Work ratios over final-grade PASS runs only;
'vs recompute' divides by the recompute-from-scratch candidate's ratio
(reference.json), so 1.0 = no better than recomputing.

| mode | problem | ended | final PASS | work ratio | vs recompute | min to first PASS | LLM turns | tokens (k) |
|---|---|---|---|---|---|---|---|---|
| orchestrator | dynamic_bfs | 3/3 | 3/3 | 0.312 | 0.651 | 21.1 | 250 | 2399.516 |
| no_reflection | dynamic_bfs | 3/3 | 2/3 | 0.659 | 1.376 | 10.0 | 206 | 1516.383 |
| harness | dynamic_bfs | 3/3 | 3/3 | 0.33 | 0.689 | 14.0 | 60 | 3314.766 |
| orchestrator | dynamic_dfs | 3/3 | 3/3 | 0.187 | 0.22 | 10.9 | 204 | 1757.557 |
| no_reflection | dynamic_dfs | 3/3 | 3/3 | 0.21 | 0.247 | 8.3 | 147 | 1153.785 |
| harness | dynamic_dfs | 3/3 | 3/3 | 0.272 | 0.321 | 7.1 | 35 | 1344.871 |
| orchestrator | dynamic_lbfs | 3/3 | 3/3 | 0.369 | 0.451 | 4.2 | 209 | 1710.276 |
| no_reflection | dynamic_lbfs | 3/3 | 3/3 | 0.474 | 0.58 | 5.3 | 182 | 1708.315 |
| harness | dynamic_lbfs | 3/3 | 3/3 | 0.168 | 0.205 | 5.4 | 41 | 2382.239 |
