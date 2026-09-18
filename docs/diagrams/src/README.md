# Diagram sources

Mermaid (mmd) sources for the figures embedded in the thesis docs. The PNGs in
`docs/diagrams/` are generated from these files; regenerate with the render API
at http://214.16.146.107:8091 (no auth).

## Render commands

POST JSON `{"kind":"mermaid","source":<file content>,"fmt":"png","width":<W>}` to
`/render`. Command used for each diagram (jq or python3 to build the body):

```bash
# architecture, deployment, loop, verification: width 1600
for f in architecture deployment loop verification; do
  python3 -c "import json;print(json.dumps({'kind':'mermaid','source':open('$f.mmd').read(),'fmt':'png','width':'1600'}))" \
    | curl -s -m 90 -X POST http://214.16.146.107:8091/render \
        -H 'Content-Type: application/json' -d @- -o ../$f.png
done

# classes: MUST use width 800, then upscale 2x (see quirk below)
python3 -c "import json;print(json.dumps({'kind':'mermaid','source':open('classes.mmd').read(),'fmt':'png','width':'800'}))" \
  | curl -s -m 90 -X POST http://214.16.146.107:8091/render \
      -H 'Content-Type: application/json' -d @- -o /tmp/classes_w800.png
python3 -c "
from PIL import Image
im = Image.open('/tmp/classes_w800.png')
im2 = im.resize((im.size[0]*2, im.size[1]*2), Image.LANCZOS)
im2.save('../classes.png')
"
```

## Known quirk: classes.mmd and render width

The classes diagram must be rendered at width 800. At widths >= 900 the render
service silently drops the `LLMProvider` box (verified at 900, 1000, 1100, 1200,
1400, 1600). After rendering at 800, upscale 2x so the embedded figure stays
crisp at full text width. Always verify the output contains all 12 class boxes
after re-rendering (LLMProvider is the one that disappears).

## Verification after regeneration

OCR the generated PNG and confirm:
- classes.png shows 12 boxes including LLMProvider (generate/repair/reflect),
  Candidate (transition/to_json/from_json), ProblemDefinition
  (check_invariant/baseline_work), Orchestrator (init/run/step_generation/stop/resume).
- The operation names in the diagram match the "The Twelve Core Classes" table
  in `docs/design.tex` section 4.2.
- No other figure embeds text that contradicts the doc prose.

After regenerating any PNG, rebuild the PDFs with `make design` / `make spec`
in the repo root (the Makefile rebuilds when diagrams change).