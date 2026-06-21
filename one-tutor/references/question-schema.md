# Question and project schema

Use UTF-8 JSON Lines for `question-bank.jsonl`: one complete JSON object per line.

## Required question fields

```json
{
  "id": "biology-cell-001",
  "topic": "Cell biology",
  "type": "single_choice",
  "stem": "Which organelle is the main site of ATP production?",
  "options": {
    "A": "Nucleus",
    "B": "Mitochondrion",
    "C": "Ribosome",
    "D": "Golgi apparatus"
  },
  "answers": ["B"],
  "explanation": "Mitochondria generate most cellular ATP through oxidative phosphorylation.",
  "source": "Chapter 3, p. 42"
}
```

- `id`: stable and unique. Keep it unchanged when wording is repaired.
- `topic`: reusable concept or chapter label.
- `type`: `single_choice`, `multiple_choice`, `true_false`, or `short_answer`.
- `stem`: self-contained prompt with no answer leakage.
- `options`: map option labels to text. Use an empty object for short answers.
- `answers`: array of correct option labels or accepted short answers.
- `explanation`: concise source-grounded reasoning.
- `source`: traceable file, section, page, URL, or record identifier.

## Optional fields

```json
{
  "accepted_answers": ["mitochondrion", "mitochondria"],
  "difficulty": "medium",
  "tags": ["energy", "organelles"],
  "independent": true,
  "status": "active",
  "grading_mode": "exact"
}
```

- Use `accepted_answers` for equivalent short responses.
- Use `difficulty` values such as `easy`, `medium`, or `hard` consistently within one project.
- Set `independent: false` when a figure, passage, or preceding question is unavailable.
- Set `status: disabled` when the key is doubtful or the item should not be selected.
- Set `grading_mode: manual` for responses that require semantic judgment.

## CSV import

Accept the same field names. Encode `options` as JSON or as pipe-separated text. Encode multiple answers with commas, slashes, Chinese enumeration commas, or pipes.

Example:

```csv
id,topic,type,stem,options,answer,explanation,source
math-001,Algebra,single_choice,What is x if x+2=5?,3|2|7|5,A,Subtract 2 from both sides.,Lesson 1
```

## Project files

```text
study-project/
├── config.json
├── question-bank.jsonl
├── history.csv
├── sessions/
│   ├── YYYY-MM-DD.json
│   ├── YYYY-MM-DD.md
│   └── YYYY-MM-DD.answers.json
└── feedback/
    └── YYYY-MM-DD.md
```

Treat `history.csv` as generated state. Do not hand-edit it unless repairing a documented data problem.
