# OneTutor

**Your private AI tutor for any subject.**

Turn notes, books, PDFs, DOCX files, course materials, or existing question banks into an adaptive study system that quizzes you, learns from your answers, and schedules what to review next.

> One learner. One tutor. Any subject.

## What it does

- Builds source-grounded question banks from your own materials
- Mixes new questions, due reviews, and weak-topic reinforcement
- Tracks both correctness and confidence
- Separates misconceptions, knowledge gaps, lucky guesses, and broken questions
- Schedules spaced review and reports mastery over time
- Keeps study data local and separate from the installed Skill

## Requirements

- Codex with Skills support
- Python 3.10 or newer
- No third-party Python packages

## Install

Clone this repository and copy the Skill into your Codex Skills directory:

```bash
git clone https://github.com/ChangjinHe2000/one-tutor.git
mkdir -p ~/.codex/skills
cp -R one-tutor/one-tutor ~/.codex/skills/one-tutor
```

Restart Codex if the Skill does not appear immediately.

## Try it

```text
Use $one-tutor to turn these study materials into a daily adaptive quiz and review workflow.
```

You can also ask:

```text
Use $one-tutor to quiz me on this PDF, grade my answers with confidence tracking, and schedule weak topics for review.
```

## How it works

```text
Your materials
    ↓
Source-grounded question bank
    ↓
New + due review + weak-topic quiz
    ↓
Answer + confidence
    ↓
Feedback + mistake diagnosis
    ↓
Next review schedule
```

The deterministic CLI handles question validation, quiz selection, grading, learning history, and spaced-review scheduling. Codex handles source understanding, question authoring, and personalized teaching feedback.

## Privacy and sharing

OneTutor does not bundle textbooks, paid courses, personal notes, or study history. Point it at materials you are allowed to use, and keep generated study projects outside the installed Skill directory.

## License

[MIT](LICENSE)
