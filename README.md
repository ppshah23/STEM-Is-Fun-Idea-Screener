# AI Idea Screener — Curriculum Pipeline Scaffold

An AI-assisted curriculum pipeline for STEM is FUN that evaluates raw project
ideas for feasibility, then drafts a classroom-ready lesson plan for those
that qualify, subject to human review before any course is finalized.

Basic framework for the STEM is FUN curriculum tool: deterministic software
owns the pipeline, Claude is called only at the judgment-heavy steps, human
review gates the output before anything renders.

See `AI_Command_Center.pptx` in this folder for the architectural pitch this
scaffold implements.

## Setup

```
pip install -r requirements.txt
```

Requires Claude API credentials — either set `ANTHROPIC_API_KEY`, or run
`ant auth login` if you have the Anthropic CLI.

## Directory structure

```
AI Command Center/
├── app.py                  # Streamlit-style entry point for the idea intake UI
├── requirements.txt
├── AI_Command_Center.pptx  # architectural pitch this scaffold implements
├── data/
│   ├── assets/
│   ├── courses/            # course JSON, authored once an idea clears intake
│   │   └── arduino-digital-io.json
│   └── personas/           # student/instructor persona JSON
│       └── middle-school-beginner.json
├── output/
│   ├── ideas/              # feasibility verdicts from pipeline.intake (generated, gitignored)
│   ├── levels/             # level classifications from pipeline.level_matrix (generated, gitignored)
│   ├── reviews/            # curriculum reviews (generated, gitignored)
│   ├── roadmaps/           # day-by-day roadmap previews from pipeline.roadmap (generated, gitignored)
│   ├── drafts/             # orchestrator run output, pending review
│   └── approved/           # drafts a human has approved
├── pipeline/
│   ├── agent.py            # the one function that calls Claude (run_skill)
│   ├── intake.py           # feasibility gate
│   ├── io.py                # deterministic load/save/export
│   ├── level_matrix.py     # grade/skill level classification
│   ├── orchestrator.py     # the fixed pipeline: analyze -> ... -> save draft
│   ├── roadmap.py          # day-by-day roadmap preview
│   ├── schemas.py          # Pydantic schemas for pipeline step output
│   ├── scoring.py
│   ├── skills.py
│   └── steps.py            # one function per agentic step
├── skills/                 # expert playbooks (Markdown) loaded as system-prompt context
│   ├── curriculum-analysis.md
│   ├── curriculum-evaluation.md
│   ├── curriculum-interview.md
│   ├── curriculum-review.md
│   ├── curriculum-roadmap.md
│   ├── grade-level-adaptation.md
│   ├── idea-feasibility.md
│   ├── idea-level-classification.md
│   ├── instructor-pedagogy.md
│   ├── lesson-planning.md
│   ├── slide-storytelling.md
│   └── worksheet-generation.md
├── tests/
│   └── test_level_matrix.py
└── web/                    # Next.js frontend for the Idea Screener
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   └── page.tsx
    └── public/
```

## Layout

- `skills/` — expert playbooks (Markdown) that get loaded as system-prompt
  context for each agentic step.
- `data/courses/`, `data/personas/` — input JSON files for a course and a
  student/instructor persona, authored once an idea clears the feasibility
  gate below.
- `pipeline/agent.py` — the one function that calls Claude (`run_skill`).
- `pipeline/intake.py` — the feasibility gate: takes a free-form idea from a
  prompter and screens it (grade fit, materials, instructor capability, AI
  assistance value, scope, safety, pedagogy) before anyone authors a course
  JSON. **Stops for human review** — it never proceeds into the main
  pipeline on its own.
- `pipeline/roadmap.py` — a rough day-by-day curriculum preview drafted
  straight from a prompter's idea (optionally informed by intake's
  feasibility notes), so the prompter can see roughly how long it'd run and
  how each session would unfold *before* anyone authors a full course JSON.
  Saved as both structured JSON and a rendered, human-readable `.md` file.
  **Stops for human review**, same as intake.
- `pipeline/steps.py` — one function per agentic step, each wired to its skill.
- `pipeline/io.py` — deterministic load/save/export functions. `export_pptx`
  and `export_worksheet` are stubs — wire up `python-pptx` / `python-docx`
  rendering there.
- `pipeline/orchestrator.py` — the fixed pipeline: analyze -> adapt -> plan ->
  outline -> evaluate -> save draft -> **stop for human review**.
- `output/ideas/` — feasibility verdicts from `pipeline.intake`, pending review.
- `output/roadmaps/` — day-by-day roadmaps (JSON + rendered `.md`) from
  `pipeline.roadmap`, pending review.
- `output/drafts/` — where an orchestrator run's output lands, pending review.
- `output/approved/` — where a draft moves once a human approves it
  (`pipeline.io.approve_draft`); a separate render step should pick up from
  here.

## Running

Screen a raw idea before authoring a course:

```
python -m pipeline.intake "<idea text>"
```

Draft a rough day-by-day roadmap preview for a raw idea (before authoring a
full course):

```
python -m pipeline.roadmap "<idea text>"
```

Run the main pipeline once a course/persona JSON exists:

```
python -m pipeline.orchestrator <course_id> <persona_id>
```

`orchestrator` will fail until you've added a course JSON and a persona JSON
for it to load.

## Next steps

1. Write real content into each file under `skills/`.
2. Add a first course + persona under `data/`.
3. Decide on and add Pydantic schemas for `run_skill`'s output per step, so
   each step's JSON is validated instead of loosely parsed.
4. Wire up `export_pptx` / `export_worksheet` in `pipeline/io.py`.
