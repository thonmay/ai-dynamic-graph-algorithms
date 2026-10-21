# Campaign eval2

Medians over ended runs. Work ratios over final-grade PASS runs only;
'vs recompute' divides by the recompute-from-scratch candidate's ratio
(reference.json), so 1.0 = no better than recomputing.

| mode | problem | ended | final PASS | work ratio | vs recompute | min to first PASS | LLM turns | tokens (k) |
|---|---|---|---|---|---|---|---|---|
| dynamic_agents | dynamic_lbfs | 3/3 | 3/3 | 0.455 | 0.557 | 3.4 | 266 | 2486.002 |
| orchestrator | dynamic_lbfs | 3/3 | 3/3 | 0.291 | 0.356 | 2.9 | 373 | 3143.515 |
