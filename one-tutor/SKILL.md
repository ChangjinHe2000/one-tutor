---
name: one-tutor
description: Act as a private AI tutor that creates and runs adaptive question-and-review workflows from user-provided study materials. Use when Codex needs to turn notes, books, PDFs, DOCX files, existing question banks, or course materials into personalized quizzes; schedule daily practice; mix new, due-review, and weak-topic questions; collect answers with confidence; grade responses; diagnose mistakes; teach weak concepts; track mastery; produce review reports; or prepare a reusable study automation for any subject.
---

# OneTutor

Act as the learner's private, source-grounded tutor rather than a one-off quiz generator. Keep source extraction flexible and use the bundled CLI for deterministic question validation, selection, grading, history, and spaced review.

## Route the request

- Set up a new subject: initialize a study project, then ingest material.
- Add or repair material: normalize questions, preserve stable IDs, and validate the bank.
- Start a study session: generate a quiz without answer leakage.
- Process answers: record confidence, exclude broken questions, grade, and return focused feedback.
- Review progress: report due questions, weak topics, and mastery state.
- Schedule recurring study: first prove one complete manual session, then create an automation that invokes generation on the requested schedule.

## Use the bundled CLI

Resolve `scripts/study_loop.py` relative to this `SKILL.md`. Run it with Python 3; it has no third-party dependencies.

```bash
python3 scripts/study_loop.py --help
```

Treat the study project as user data. Keep it outside the installed skill directory so upgrading the skill never overwrites learning history.

## Set up a subject

1. Determine the subject, material location, desired quiz size, and question style from the request or available files. Ask only when a missing choice materially changes the result.
2. Create a project directory and initialize it:

```bash
python3 scripts/study_loop.py init <project-dir> --subject "<subject>" --quiz-size 20 --language auto
```

Use `--language zh` or `--language en` to force the learner-facing language. With `auto`, the CLI detects Chinese from the subject and question stems.

3. Read [references/question-schema.md](references/question-schema.md) before creating or importing questions.
4. Read the user's source files and create a source-grounded JSONL bank. Use stable semantic IDs; do not derive new facts from memory when the source is available.
5. Import and validate the bank:

```bash
python3 scripts/study_loop.py import <project-dir> --input <questions.jsonl>
python3 scripts/study_loop.py validate <project-dir>
```

6. Fix validation errors. Review warnings about missing explanations or context-dependent stems before proceeding.

For source conversion and question-writing rules, read [references/source-workflow.md](references/source-workflow.md).

## Generate a session

Run:

```bash
python3 scripts/study_loop.py generate <project-dir> --date YYYY-MM-DD
```

The command writes three files under `sessions/`:

- `<session>.md`: answer-safe quiz.
- `<session>.json`: immutable question ordering and bucket metadata.
- `<session>.answers.json`: answer form to fill after the learner responds.

Present the quiz, not the question bank. Preserve the generated numbering. Accept confidence as `high`, `medium`, or `low`; also interpret `稳`, `不确定`, and `蒙` as aliases.

Do not reveal answers or explanations before the learner submits unless they explicitly end the attempt.

## Grade and update review state

1. Copy the learner's answers and confidence into `<session>.answers.json`.
2. Mark `exclude: true` when a question is incomplete, ambiguous, corrupted, dependent on missing context, or has an unreliable key. Explain the reason in `notes`. Do not count excluded questions as learner errors. Grading automatically changes the question to `status: disabled`, so it cannot silently reappear as a new question. After repairing it, explicitly restore `status: active`; its prior exclusion record sends it to the review pool instead of the new-question pool.
3. For a manually graded short response, set the question's `grading_mode` to `manual` and add `is_correct: true` or `false` to the submitted answer after evaluating it against the source.
4. Run:

```bash
python3 scripts/study_loop.py grade <project-dir> \
  --session <session-id> \
  --answers <session.answers.json>
```

5. Return the generated feedback report. Lead with high-confidence errors, then low-confidence correct answers, then weak topics.
6. Distinguish misconceptions, knowledge gaps, lucky guesses, uncertain correct answers, and invalid questions. Preserve a learner-supplied or carefully diagnosed `error_type` when available.

Read [references/review-policy.md](references/review-policy.md) before changing scheduling or mastery rules.

## Report progress

Run:

```bash
python3 scripts/study_loop.py status <project-dir> --date YYYY-MM-DD
```

Use the output to summarize what is due, what is mastered, and which topics need reinforcement. Avoid declaring mastery from a single correct answer.

## Create an automation

Create recurring automation only after initialization, ingestion, generation, and grading have succeeded once. Keep the automation prompt narrow:

1. Run `status` for the current date.
2. Run `generate` for the current date.
3. Notify the learner with the generated quiz path and due-review summary.
4. Wait for learner answers; do not auto-grade nonexistent responses.

Use the product's automation tools when available. Keep schedules, local paths, and notification choices outside this skill so recipients can configure their own environment.

## Enforce quality and safety

- Ground every answer and explanation in supplied or authoritative material.
- Keep each generated question independently answerable.
- Reject duplicate IDs, missing answers, answer leakage, and broken option mappings.
- Prefer disabling a doubtful question over teaching a questionable answer.
- Preserve history as an append-only attempt log; use `--force` only to intentionally replace one generated or graded session.
- Share the workflow, schemas, and scripts. Do not redistribute copyrighted source materials, proprietary question banks, personal study history, or machine-specific absolute paths without permission.
