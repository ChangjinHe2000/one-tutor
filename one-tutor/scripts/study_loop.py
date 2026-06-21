#!/usr/bin/env python3
"""Deterministic adaptive quiz and spaced-review workflow.

The script intentionally uses only the Python standard library so a shared
skill can run without installing dependencies. Codex handles source reading
and question authoring; this tool owns normalization, selection, grading,
history, scheduling, and reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


QUESTION_TYPES = {"single_choice", "multiple_choice", "true_false", "short_answer"}
CONFIDENCE_ALIASES = {
    "high": "high",
    "medium": "medium",
    "low": "low",
    "稳": "high",
    "确定": "high",
    "不确定": "medium",
    "蒙": "low",
    "guess": "low",
}
HISTORY_FIELDS = [
    "session_id",
    "session_date",
    "question_id",
    "topic",
    "bucket",
    "user_answer",
    "confidence",
    "is_correct",
    "error_type",
    "mastery",
    "repetitions",
    "interval_days",
    "ease",
    "next_review",
    "notes",
]
CONTEXT_RISK_RE = re.compile(
    r"\b(?:above|below|previous question|following figure|shown in the figure)\b|"
    r"上图|下图|如下图|承接上题|上一题|如前所述",
    re.IGNORECASE,
)
ANSWER_LEAK_RE = re.compile(r"(?:correct answer|答案|正确答案)\s*[:：]", re.IGNORECASE)


def fail(message: str) -> None:
    raise SystemExit(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        fail(f"Expected date in YYYY-MM-DD format, got: {value}")


def today_iso() -> str:
    return date.today().isoformat()


def project_paths(project: Path) -> dict[str, Path]:
    return {
        "config": project / "config.json",
        "bank": project / "question-bank.jsonl",
        "history": project / "history.csv",
        "sessions": project / "sessions",
        "feedback": project / "feedback",
    }


def normalize_answers(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,，/、|]+", text) if part.strip()]


def normalize_options(value: Any) -> dict[str, str]:
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            parts = [part.strip() for part in text.split("|") if part.strip()]
            value = {chr(65 + index): part for index, part in enumerate(parts)}
    if isinstance(value, list):
        return {chr(65 + index): str(item).strip() for index, item in enumerate(value)}
    if isinstance(value, dict):
        return {str(key).strip().upper(): str(text).strip() for key, text in value.items()}
    return {}


def canonicalize_question(raw: dict[str, Any]) -> dict[str, Any]:
    question_type = str(raw.get("type", "single_choice")).strip()
    status = str(raw.get("status", "active")).strip()
    independent = raw.get("independent", True)
    if isinstance(independent, str):
        independent = independent.strip().lower() not in {"false", "0", "no", "否"}
    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [item.strip() for item in re.split(r"[,，|]", tags) if item.strip()]
    answers = normalize_answers(raw.get("answers", raw.get("answer")))
    return {
        "id": str(raw.get("id", "")).strip(),
        "topic": str(raw.get("topic", "")).strip(),
        "type": question_type,
        "stem": str(raw.get("stem", "")).strip(),
        "options": normalize_options(raw.get("options")),
        "answers": answers,
        "accepted_answers": normalize_answers(raw.get("accepted_answers", answers)),
        "explanation": str(raw.get("explanation", "")).strip(),
        "source": str(raw.get("source", "")).strip(),
        "difficulty": str(raw.get("difficulty", "medium")).strip(),
        "tags": tags if isinstance(tags, list) else [],
        "independent": bool(independent),
        "status": status,
        "grading_mode": str(raw.get("grading_mode", "exact")).strip(),
    }


def validate_questions(questions: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for index, q in enumerate(questions, start=1):
        label = q.get("id") or f"row {index}"
        if not q.get("id"):
            errors.append(f"row {index}: missing id")
        elif q["id"] in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(q.get("id", ""))
        if not q.get("topic"):
            errors.append(f"{label}: missing topic")
        if q.get("type") not in QUESTION_TYPES:
            errors.append(f"{label}: unsupported type {q.get('type')!r}")
        if not q.get("stem"):
            errors.append(f"{label}: missing stem")
        if q.get("type") in {"single_choice", "multiple_choice", "true_false"}:
            options = q.get("options", {})
            if len(options) < 2:
                errors.append(f"{label}: objective question needs at least two options")
            missing = [answer for answer in q.get("answers", []) if answer.upper() not in options]
            if missing:
                errors.append(f"{label}: answers not found in options: {missing}")
        if not q.get("answers") and q.get("grading_mode") != "manual":
            errors.append(f"{label}: missing answers")
        if q.get("type") == "single_choice" and len(q.get("answers", [])) != 1:
            errors.append(f"{label}: single_choice requires exactly one answer")
        if CONTEXT_RISK_RE.search(q.get("stem", "")):
            warnings.append(f"{label}: stem may depend on missing context")
        if ANSWER_LEAK_RE.search(q.get("stem", "")):
            errors.append(f"{label}: stem appears to leak the answer")
        if not q.get("explanation"):
            warnings.append(f"{label}: missing explanation")
        if not q.get("independent", True) and q.get("status") == "active":
            warnings.append(f"{label}: active but marked non-independent; generation will skip it")
    return errors, warnings


def load_bank(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        fail(f"Missing question bank: {path}")
    questions: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"Invalid JSONL at {path}:{number}: {exc}")
        if not isinstance(raw, dict):
            fail(f"Expected an object at {path}:{number}")
        questions.append(canonicalize_question(raw))
    return questions


def write_bank(path: Path, questions: Iterable[dict[str, Any]]) -> None:
    text = "\n".join(json.dumps(q, ensure_ascii=False, separators=(",", ":")) for q in questions)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def load_import_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return load_bank(path)
    if suffix == ".json":
        raw = read_json(path)
        if not isinstance(raw, list):
            fail("A JSON question bank must contain an array of question objects")
        return [canonicalize_question(item) for item in raw]
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [canonicalize_question(row) for row in csv.DictReader(handle)]
    fail("Question bank input must be .jsonl, .json, or .csv")


def demo_questions() -> list[dict[str, Any]]:
    raw = [
        {"id": "demo-math-001", "topic": "Arithmetic", "type": "single_choice", "stem": "What is 7 × 8?", "options": {"A": "54", "B": "56", "C": "64", "D": "72"}, "answer": "B", "explanation": "7 × 8 = 56.", "source": "Skill demo"},
        {"id": "demo-math-002", "topic": "Arithmetic", "type": "short_answer", "stem": "What is 15 − 9?", "answer": "6", "explanation": "Subtract 9 from 15 to get 6.", "source": "Skill demo"},
        {"id": "demo-science-001", "topic": "Biology", "type": "single_choice", "stem": "Which organelle is the main site of photosynthesis?", "options": {"A": "Nucleus", "B": "Ribosome", "C": "Chloroplast", "D": "Golgi apparatus"}, "answer": "C", "explanation": "Photosynthesis mainly occurs in chloroplasts.", "source": "Skill demo"},
        {"id": "demo-science-002", "topic": "Physics", "type": "true_false", "stem": "Sound can travel through a vacuum.", "options": {"A": "True", "B": "False"}, "answer": "B", "explanation": "Sound needs a material medium.", "source": "Skill demo"},
        {"id": "demo-history-001", "topic": "History", "type": "single_choice", "stem": "Which civilization built Machu Picchu?", "options": {"A": "Maya", "B": "Inca", "C": "Roman", "D": "Egyptian"}, "answer": "B", "explanation": "Machu Picchu was built by the Inca civilization.", "source": "Skill demo"},
        {"id": "demo-language-001", "topic": "Language", "type": "multiple_choice", "stem": "Which words are nouns?", "options": {"A": "river", "B": "quickly", "C": "idea", "D": "blue"}, "answers": ["A", "C"], "explanation": "River and idea function as nouns here.", "source": "Skill demo"},
    ]
    return [canonicalize_question(item) for item in raw]


def load_config(project: Path) -> dict[str, Any]:
    config = read_json(project_paths(project)["config"])
    if not isinstance(config, dict):
        fail("config.json must contain an object")
    return config


def read_history(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_history(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def latest_states(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    states: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("question_id") and row.get("is_correct") in {"true", "false"}:
            states[row["question_id"]] = row
    return states


def weak_topic_scores(rows: list[dict[str, str]]) -> list[tuple[str, float]]:
    totals: dict[str, float] = defaultdict(float)
    attempts: dict[str, int] = defaultdict(int)
    for row in rows:
        topic = row.get("topic", "")
        if not topic or row.get("is_correct") not in {"true", "false"}:
            continue
        attempts[topic] += 1
        if row["is_correct"] == "false":
            totals[topic] += 2.0
        elif row.get("confidence") == "low":
            totals[topic] += 1.0
        elif row.get("confidence") == "medium":
            totals[topic] += 0.4
    scored = [(topic, score / math.sqrt(attempts[topic])) for topic, score in totals.items()]
    return sorted(scored, key=lambda item: (-item[1], item[0]))


def allocate_counts(total: int, mix: dict[str, Any]) -> dict[str, int]:
    buckets = ["new", "review", "weak"]
    weights = {bucket: max(0.0, float(mix.get(bucket, 0))) for bucket in buckets}
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        fail("At least one quiz mix weight must be positive")
    raw = {bucket: total * weights[bucket] / weight_sum for bucket in buckets}
    counts = {bucket: int(math.floor(raw[bucket])) for bucket in buckets}
    for bucket in sorted(buckets, key=lambda key: raw[key] - counts[key], reverse=True):
        if sum(counts.values()) >= total:
            break
        counts[bucket] += 1
    return counts


def select_questions(
    questions: list[dict[str, Any]],
    history: list[dict[str, str]],
    config: dict[str, Any],
    session_id: str,
    session_date: date,
    requested: int,
) -> list[dict[str, Any]]:
    eligible = [q for q in questions if q["status"] == "active" and q["independent"]]
    if requested > len(eligible):
        fail(f"Requested {requested} questions, but only {len(eligible)} active independent questions exist")
    states = latest_states(history)
    weak_topics = [topic for topic, score in weak_topic_scores(history) if score > 0][:5]
    seed = f"{config.get('seed_salt', '')}|{config.get('subject', '')}|{session_id}"
    rng = random.Random(seed)

    def randomized(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        result = list(items)
        rng.shuffle(result)
        return result

    new_pool = randomized(q for q in eligible if q["id"] not in states)
    review_pool = randomized(
        q
        for q in eligible
        if q["id"] in states
        and states[q["id"]].get("next_review", "9999-12-31") <= session_date.isoformat()
    )
    weak_pool = randomized(
        q
        for topic in weak_topics
        for q in eligible
        if q["topic"] == topic and states.get(q["id"], {}).get("mastery") != "mastered"
    )
    targets = allocate_counts(requested, config.get("mix", {}))
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def take(bucket: str, pool: Iterable[dict[str, Any]], limit: int) -> None:
        taken = 0
        for question in pool:
            if taken >= limit:
                return
            if question["id"] in selected_ids:
                continue
            selected.append({"bucket": bucket, "question": question})
            selected_ids.add(question["id"])
            taken += 1

    take("new", new_pool, targets["new"])
    take("review", review_pool, targets["review"])
    take("weak", weak_pool, targets["weak"])

    remaining = requested - len(selected)
    for bucket, pool in (("review", review_pool), ("new", new_pool), ("weak", weak_pool)):
        remaining = requested - len(selected)
        if remaining:
            take(bucket, pool, remaining)
    remaining = requested - len(selected)
    if remaining:
        take("fill", randomized(eligible), remaining)
    return selected


def render_quiz(subject: str, session_id: str, selected: list[dict[str, Any]]) -> str:
    lines = [
        f"# {subject} · Adaptive Quiz ({session_id})",
        "",
        "Answer every question and record confidence as `high`, `medium`, or `low`.",
        "Do not inspect the question bank while answering.",
        "",
    ]
    for number, item in enumerate(selected, start=1):
        q = item["question"]
        lines.extend([f"## {number}. [{q['topic']}]", "", q["stem"], ""])
        for key, value in q["options"].items():
            lines.append(f"- {key}. {value}")
        if not q["options"]:
            lines.append("Answer: ______________________________")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def normalize_confidence(value: Any) -> str:
    normalized = CONFIDENCE_ALIASES.get(str(value).strip().lower())
    if not normalized:
        normalized = CONFIDENCE_ALIASES.get(str(value).strip())
    if not normalized:
        fail(f"Unsupported confidence {value!r}; use high, medium, or low")
    return normalized


def normalized_choice(value: Any) -> list[str]:
    if isinstance(value, list):
        parts = value
    else:
        parts = re.split(r"[,，/、\s]+", str(value).strip())
    return sorted({str(part).strip().upper() for part in parts if str(part).strip()})


def grade_value(q: dict[str, Any], answer: Any, manual_result: Any) -> bool | None:
    if q.get("grading_mode") == "manual":
        if isinstance(manual_result, bool):
            return manual_result
        return None
    if q["type"] in {"single_choice", "multiple_choice", "true_false"}:
        return normalized_choice(answer) == normalized_choice(q["answers"])
    candidate = re.sub(r"\s+", " ", str(answer).strip()).casefold()
    accepted = {re.sub(r"\s+", " ", item.strip()).casefold() for item in q["accepted_answers"]}
    return candidate in accepted


def schedule(
    previous: dict[str, str] | None,
    correct: bool,
    confidence: str,
    session_date: date,
) -> dict[str, Any]:
    previous = previous or {}
    old_repetitions = int(float(previous.get("repetitions") or 0))
    old_interval = int(float(previous.get("interval_days") or 0))
    ease = float(previous.get("ease") or 2.5)
    if not correct:
        repetitions = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
        mastery = "needs-review"
    else:
        quality = {"low": 3, "medium": 4, "high": 5}[confidence]
        repetitions = old_repetitions + 1
        if old_repetitions == 0:
            interval = 1
        elif old_repetitions == 1:
            interval = 3
        else:
            interval = max(1, round(max(old_interval, 1) * ease))
        ease = max(1.3, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if confidence == "low":
            interval = min(interval, 2)
            mastery = "reinforcing"
        elif confidence == "medium":
            interval = min(interval, 7)
            mastery = "reinforcing"
        elif repetitions >= 3 and interval >= 7:
            mastery = "mastered"
        else:
            mastery = "learning"
    return {
        "repetitions": repetitions,
        "interval_days": interval,
        "ease": round(ease, 2),
        "next_review": (session_date + timedelta(days=interval)).isoformat(),
        "mastery": mastery,
    }


def inferred_error_type(correct: bool, confidence: str, supplied: str) -> str:
    if supplied:
        return supplied
    if not correct:
        return "misconception" if confidence == "high" else "knowledge-gap"
    if confidence == "low":
        return "lucky-guess"
    if confidence == "medium":
        return "uncertain-correct"
    return ""


def display_answer(q: dict[str, Any]) -> str:
    pieces: list[str] = []
    for answer in q["answers"]:
        option_text = q["options"].get(answer.upper())
        pieces.append(f"{answer} ({option_text})" if option_text else answer)
    return ", ".join(pieces)


def command_init(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    paths = project_paths(project)
    if paths["config"].exists() and not args.force:
        fail(f"Project already initialized: {project}")
    project.mkdir(parents=True, exist_ok=True)
    paths["sessions"].mkdir(exist_ok=True)
    paths["feedback"].mkdir(exist_ok=True)
    config = {
        "subject": args.subject,
        "quiz_size": args.quiz_size,
        "mix": {"new": 0.5, "review": 0.35, "weak": 0.15},
        "seed_salt": "one-tutor",
        "confidence_labels": ["high", "medium", "low"],
    }
    write_json(paths["config"], config)
    write_bank(paths["bank"], demo_questions() if args.with_demo else [])
    if not paths["history"].exists() or args.force:
        write_history(paths["history"], [])
    print(f"Initialized study project: {project}")


def command_import(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    paths = project_paths(project)
    load_config(project)
    incoming = load_import_file(Path(args.input).expanduser().resolve())
    errors, warnings = validate_questions(incoming)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        fail("Question bank validation failed:\n- " + "\n- ".join(errors))
    existing = [] if args.replace else load_bank(paths["bank"])
    merged = {q["id"]: q for q in existing}
    merged.update({q["id"]: q for q in incoming})
    write_bank(paths["bank"], merged.values())
    print(f"Imported {len(incoming)} questions; bank now contains {len(merged)}")


def command_validate(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    questions = load_bank(project_paths(project)["bank"])
    errors, warnings = validate_questions(questions)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        fail("Validation failed:\n- " + "\n- ".join(errors))
    active = sum(q["status"] == "active" and q["independent"] for q in questions)
    print(f"Valid question bank: {len(questions)} total, {active} active and independent")


def command_generate(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    paths = project_paths(project)
    config = load_config(project)
    questions = load_bank(paths["bank"])
    errors, warnings = validate_questions(questions)
    if errors:
        fail("Fix the question bank before generating:\n- " + "\n- ".join(errors))
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    session_id = args.session or args.date
    session_date = parse_iso_date(args.date)
    requested = args.size or int(config.get("quiz_size", 20))
    selected = select_questions(
        questions,
        read_history(paths["history"]),
        config,
        session_id,
        session_date,
        requested,
    )
    session_path = paths["sessions"] / f"{session_id}.json"
    if session_path.exists() and not args.force:
        fail(f"Session already exists: {session_path}; pass --force to replace it")
    session = {
        "session_id": session_id,
        "date": args.date,
        "subject": config.get("subject", "Study"),
        "questions": [
            {"number": number, "question_id": item["question"]["id"], "bucket": item["bucket"]}
            for number, item in enumerate(selected, start=1)
        ],
    }
    write_json(session_path, session)
    quiz_path = paths["sessions"] / f"{session_id}.md"
    quiz_path.write_text(render_quiz(session["subject"], session_id, selected), encoding="utf-8")
    answers_path = paths["sessions"] / f"{session_id}.answers.json"
    write_json(
        answers_path,
        {
            "session_id": session_id,
            "answers": [
                {
                    "number": item["number"],
                    "answer": "",
                    "confidence": "medium",
                    "exclude": False,
                    "notes": "",
                }
                for item in session["questions"]
            ],
        },
    )
    bucket_counts: dict[str, int] = defaultdict(int)
    for item in selected:
        bucket_counts[item["bucket"]] += 1
    print(f"Generated {len(selected)} questions: {dict(bucket_counts)}")
    print(quiz_path)
    print(answers_path)


def command_grade(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    paths = project_paths(project)
    session = read_json(paths["sessions"] / f"{args.session}.json")
    submitted = read_json(Path(args.answers).expanduser().resolve())
    submitted_items = submitted.get("answers", submitted) if isinstance(submitted, dict) else submitted
    if not isinstance(submitted_items, list):
        fail("Answers file must be a list or an object containing an answers list")
    by_number = {int(item["number"]): item for item in submitted_items if isinstance(item, dict) and "number" in item}
    questions = {q["id"]: q for q in load_bank(paths["bank"])}
    history = read_history(paths["history"])
    if any(row.get("session_id") == args.session for row in history):
        if not args.force:
            fail(f"Session {args.session} has already been graded; pass --force to regrade")
        history = [row for row in history if row.get("session_id") != args.session]
    states = latest_states(history)
    session_date = parse_iso_date(session["date"])
    results: list[dict[str, Any]] = []
    for item in session["questions"]:
        number = int(item["number"])
        if number not in by_number:
            fail(f"Missing answer for question {number}")
        answer_item = by_number[number]
        q = questions.get(item["question_id"])
        if not q:
            fail(f"Question no longer exists in bank: {item['question_id']}")
        confidence = normalize_confidence(answer_item.get("confidence", ""))
        if bool(answer_item.get("exclude", False)):
            results.append({"number": number, "question": q, "excluded": True})
            history.append(
                {
                    "session_id": args.session,
                    "session_date": session["date"],
                    "question_id": q["id"],
                    "topic": q["topic"],
                    "bucket": item["bucket"],
                    "user_answer": str(answer_item.get("answer", "")),
                    "confidence": confidence,
                    "is_correct": "",
                    "error_type": "invalid-question",
                    "mastery": "excluded",
                    "repetitions": states.get(q["id"], {}).get("repetitions", "0"),
                    "interval_days": "0",
                    "ease": states.get(q["id"], {}).get("ease", "2.5"),
                    "next_review": "",
                    "notes": str(answer_item.get("notes", "")),
                }
            )
            continue
        submitted_answer = answer_item.get("answer", "")
        if submitted_answer is None or submitted_answer == "" or submitted_answer == []:
            fail(f"Question {number} has no submitted answer; fill it or set exclude to true")
        correct = grade_value(q, submitted_answer, answer_item.get("is_correct"))
        if correct is None:
            results.append({"number": number, "question": q, "manual": True})
            history.append(
                {
                    "session_id": args.session,
                    "session_date": session["date"],
                    "question_id": q["id"],
                    "topic": q["topic"],
                    "bucket": item["bucket"],
                    "user_answer": str(answer_item.get("answer", "")),
                    "confidence": confidence,
                    "is_correct": "",
                    "error_type": "manual-review-required",
                    "mastery": "ungraded",
                    "repetitions": states.get(q["id"], {}).get("repetitions", "0"),
                    "interval_days": "0",
                    "ease": states.get(q["id"], {}).get("ease", "2.5"),
                    "next_review": session["date"],
                    "notes": str(answer_item.get("notes", "")),
                }
            )
            continue
        spaced = schedule(states.get(q["id"]), correct, confidence, session_date)
        error_type = inferred_error_type(correct, confidence, str(answer_item.get("error_type", "")).strip())
        row = {
            "session_id": args.session,
            "session_date": session["date"],
            "question_id": q["id"],
            "topic": q["topic"],
            "bucket": item["bucket"],
            "user_answer": json.dumps(answer_item.get("answer", ""), ensure_ascii=False) if isinstance(answer_item.get("answer"), list) else str(answer_item.get("answer", "")),
            "confidence": confidence,
            "is_correct": str(correct).lower(),
            "error_type": error_type,
            "mastery": spaced["mastery"],
            "repetitions": spaced["repetitions"],
            "interval_days": spaced["interval_days"],
            "ease": spaced["ease"],
            "next_review": spaced["next_review"],
            "notes": str(answer_item.get("notes", "")),
        }
        history.append(row)
        states[q["id"]] = {key: str(value) for key, value in row.items()}
        results.append(
            {
                "number": number,
                "question": q,
                "answer": answer_item.get("answer", ""),
                "confidence": confidence,
                "correct": correct,
                "error_type": error_type,
                "next_review": spaced["next_review"],
            }
        )
    write_history(paths["history"], history)

    graded = [result for result in results if not result.get("manual") and not result.get("excluded")]
    correct_count = sum(result["correct"] for result in graded)
    wrong = [result for result in graded if not result["correct"]]
    uncertain = [result for result in graded if result["correct"] and result["confidence"] != "high"]
    manual = [result for result in results if result.get("manual")]
    excluded = [result for result in results if result.get("excluded")]
    lines = [
        f"# {session.get('subject', 'Study')} · Feedback ({args.session})",
        "",
        f"- Score: {correct_count}/{len(graded)}" if graded else "- Score: pending manual review",
        f"- Incorrect: {len(wrong)}",
        f"- Correct but uncertain: {len(uncertain)}",
        f"- Manual review required: {len(manual)}",
        f"- Invalid/excluded questions: {len(excluded)}",
        "",
        "## Review first",
        "",
    ]
    focus = wrong + uncertain
    if not focus:
        lines.append("No automatically graded questions require immediate review.")
        lines.append("")
    for result in focus:
        q = result["question"]
        lines.extend(
            [
                f"### Question {result['number']} · {q['topic']}",
                "",
                f"- Your answer: {result['answer']}",
                f"- Correct answer: {display_answer(q)}",
                f"- Confidence: {result['confidence']}",
                f"- Classification: {result['error_type'] or 'correct'}",
                f"- Next review: {result['next_review']}",
                f"- Explanation: {q['explanation'] or 'Add an explanation to the question bank.'}",
                "",
            ]
        )
    if manual:
        lines.extend(["## Manual review", ""])
        for result in manual:
            lines.append(f"- Question {result['number']} ({result['question']['id']})")
        lines.append("")
    if excluded:
        lines.extend(["## Invalid or excluded questions", ""])
        for result in excluded:
            lines.append(f"- Question {result['number']} ({result['question']['id']})")
        lines.append("")
    topic_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for result in graded:
        topic_stats[result["question"]["topic"]][1] += 1
        topic_stats[result["question"]["topic"]][0] += int(result["correct"])
    lines.extend(["## Topic performance", ""])
    for topic, (right, total) in sorted(topic_stats.items(), key=lambda item: (item[1][0] / item[1][1], item[0])):
        lines.append(f"- {topic}: {right}/{total}")
    lines.append("")
    feedback_path = paths["feedback"] / f"{args.session}.md"
    feedback_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Graded {len(graded)} questions: {correct_count} correct, {len(wrong)} incorrect")
    print(feedback_path)


def command_status(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    paths = project_paths(project)
    config = load_config(project)
    questions = load_bank(paths["bank"])
    history = read_history(paths["history"])
    states = latest_states(history)
    on_date = parse_iso_date(args.date)
    active = [q for q in questions if q["status"] == "active" and q["independent"]]
    due = [q for q in active if q["id"] in states and states[q["id"]].get("next_review", "9999-12-31") <= on_date.isoformat()]
    mastered = [q for q in active if states.get(q["id"], {}).get("mastery") == "mastered"]
    weak = weak_topic_scores(history)[:5]
    print(f"Subject: {config.get('subject', '')}")
    print(f"Question bank: {len(questions)} total, {len(active)} active")
    print(f"Progress: {len(states)} seen, {len(mastered)} mastered, {len(due)} due on {args.date}")
    print("Weak topics: " + (", ".join(f"{topic} ({score:.2f})" for topic, score in weak) or "none yet"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a study project")
    init_parser.add_argument("project")
    init_parser.add_argument("--subject", required=True)
    init_parser.add_argument("--quiz-size", type=int, default=20)
    init_parser.add_argument("--with-demo", action="store_true")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=command_init)

    import_parser = subparsers.add_parser("import", help="Import JSONL, JSON, or CSV questions")
    import_parser.add_argument("project")
    import_parser.add_argument("--input", required=True)
    import_parser.add_argument("--replace", action="store_true")
    import_parser.set_defaults(func=command_import)

    validate_parser = subparsers.add_parser("validate", help="Validate a project's question bank")
    validate_parser.add_argument("project")
    validate_parser.set_defaults(func=command_validate)

    generate_parser = subparsers.add_parser("generate", help="Generate an adaptive quiz")
    generate_parser.add_argument("project")
    generate_parser.add_argument("--date", default=today_iso())
    generate_parser.add_argument("--session")
    generate_parser.add_argument("--size", type=int)
    generate_parser.add_argument("--force", action="store_true")
    generate_parser.set_defaults(func=command_generate)

    grade_parser = subparsers.add_parser("grade", help="Grade answers and update review history")
    grade_parser.add_argument("project")
    grade_parser.add_argument("--session", required=True)
    grade_parser.add_argument("--answers", required=True)
    grade_parser.add_argument("--force", action="store_true")
    grade_parser.set_defaults(func=command_grade)

    status_parser = subparsers.add_parser("status", help="Show study progress and due reviews")
    status_parser.add_argument("project")
    status_parser.add_argument("--date", default=today_iso())
    status_parser.set_defaults(func=command_status)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
