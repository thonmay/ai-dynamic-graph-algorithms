# Campaign eval2

Medians over ended runs. Work ratios over final-grade PASS runs only;
'vs recompute' divides by the recompute-from-scratch candidate's ratio
(reference.json), so 1.0 = no better than recomputing.

| mode | problem | ended | final PASS | work ratio | vs recompute | min to first PASS | LLM turns | tokens (k) |
|---|---|---|---|---|---|---|---|---|
| dynamic_agents | dynamic_lbfs | 8/8 | 8/8 | 0.356 | 0.435 | 4.7 | 298.0 | 3246.391 |
| orchestrator | dynamic_lbfs | 8/8 | 7/8 | 0.366 | 0.448 | 4.8 | 291.0 | 2596.749 |
