# Campaign eval3

Medians over ended runs. Work ratios over final-grade PASS runs only;
'vs recompute' divides by the recompute-from-scratch candidate's ratio
(reference.json), so 1.0 = no better than recomputing.

| mode | problem | ended | final PASS | work ratio | vs recompute | min to first PASS | LLM turns | tokens (k) |
|---|---|---|---|---|---|---|---|---|
| orchestrator | dynamic_bfs | 1/1 | 1/1 | 0.16 | 0.333 | 0.6 | 37 | 89.97 |
| no_reflection | dynamic_bfs | 1/1 | 1/1 | 0.159 | 0.333 | 0.6 | 33 | 79.135 |
| harness | dynamic_bfs | 1/1 | 0/1 | - | - | 0.3 | 16 | 389.031 |
| orchestrator | dynamic_dfs | 1/1 | 1/1 | 0.203 | 0.239 | 0.6 | 36 | 78.82 |
| no_reflection | dynamic_dfs | 1/1 | 1/1 | 0.304 | 0.358 | 0.6 | 33 | 65.854 |
| harness | dynamic_dfs | 1/1 | 0/1 | - | - | 0.4 | 18 | 407.034 |
| orchestrator | dynamic_lbfs | 1/1 | 1/1 | 0.636 | 0.778 | 0.8 | 33 | 74.619 |
| no_reflection | dynamic_lbfs | 1/1 | 1/1 | 0.17 | 0.208 | 0.7 | 34 | 71.333 |
| harness | dynamic_lbfs | 1/1 | 1/1 | 0.616 | 0.753 | 0.3 | 16 | 358.484 |
