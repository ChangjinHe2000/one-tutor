#!/usr/bin/env python3
"""Regenerate the public OneTutor soft-exam demonstration."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "one-tutor" / "scripts" / "study_loop.py"
BANK = Path(__file__).with_name("question-bank.jsonl")
RESULTS = Path(__file__).with_name("results")


def run(*args: object) -> str:
    completed = subprocess.run(
        [sys.executable, str(CLI), *map(str, args)],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def normalize(text: str, project: Path) -> str:
    project_paths = sorted({str(project), str(project.resolve())}, key=len, reverse=True)
    for path in project_paths:
        text = text.replace(path, "<demo-project>")
    return text.replace(str(BANK), "examples/soft-exam/question-bank.jsonl")


def wrong_option(question: dict[str, object]) -> str:
    answers = set(question["answers"])
    return next(option for option in question["options"] if option not in answers)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    bank = {
        item["id"]: item
        for item in (json.loads(line) for line in BANK.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    transcript: list[tuple[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="one-tutor-soft-exam-") as temp_dir:
        project = Path(temp_dir) / "project"

        commands = [
            (
                f'init <demo-project> --subject "软件设计师考试" --quiz-size 6 --language zh',
                ("init", project, "--subject", "软件设计师考试", "--quiz-size", 6, "--language", "zh"),
            ),
            (
                "import <demo-project> --input examples/soft-exam/question-bank.jsonl --replace",
                ("import", project, "--input", BANK, "--replace"),
            ),
            ("validate <demo-project>", ("validate", project)),
            (
                "generate <demo-project> --date 2026-06-01 --session round-1 --size 6",
                ("generate", project, "--date", "2026-06-01", "--session", "round-1", "--size", 6),
            ),
        ]
        for shown, actual in commands:
            transcript.append((shown, normalize(run(*actual), project)))

        session = json.loads((project / "sessions" / "round-1.json").read_text(encoding="utf-8"))
        answers = []
        for index, item in enumerate(session["questions"]):
            question = bank[item["question_id"]]
            if index == 0:
                answer = wrong_option(question)
                confidence = "稳"
                notes = "演示：有把握但答错，用于识别概念误解"
            elif index == 1:
                answer = question["answers"][0]
                confidence = "蒙"
                notes = "演示：答对但信心很低，用于识别蒙对"
            elif index == 2:
                answer = question["answers"][0]
                confidence = "不确定"
                notes = "演示：答对但仍需巩固"
            else:
                answer = question["answers"][0]
                confidence = "稳"
                notes = ""
            answers.append(
                {
                    "number": item["number"],
                    "answer": answer,
                    "confidence": confidence,
                    "exclude": False,
                    "notes": notes,
                }
            )

        answers_path = project / "sessions" / "round-1.answers.json"
        answers_path.write_text(
            json.dumps({"session_id": "round-1", "answers": answers}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        transcript.append(
            (
                "grade <demo-project> --session round-1 --answers <demo-project>/sessions/round-1.answers.json",
                normalize(run("grade", project, "--session", "round-1", "--answers", answers_path), project),
            )
        )
        status = run("status", project, "--date", "2026-06-02")
        transcript.append(("status <demo-project> --date 2026-06-02", normalize(status, project)))
        transcript.append(
            (
                "generate <demo-project> --date 2026-06-02 --session round-2 --size 6",
                normalize(
                    run("generate", project, "--date", "2026-06-02", "--session", "round-2", "--size", 6),
                    project,
                ),
            )
        )

        artifacts = {
            "01-round-1-quiz.md": project / "sessions" / "round-1.md",
            "02-round-1-answers.json": answers_path,
            "03-round-1-feedback.md": project / "feedback" / "round-1.md",
            "04-round-2-quiz.md": project / "sessions" / "round-2.md",
            "05-round-2-session.json": project / "sessions" / "round-2.json",
            "06-history.csv": project / "history.csv",
        }
        for destination, source in artifacts.items():
            shutil.copyfile(source, RESULTS / destination)
        history_path = RESULTS / "06-history.csv"
        history_path.write_text(history_path.read_text(encoding="utf-8-sig"), encoding="utf-8", newline="\n")
        (RESULTS / "status.txt").write_text(status + "\n", encoding="utf-8")

    lines = ["# 可复现的命令与真实输出", ""]
    for command, output in transcript:
        lines.extend(
            [
                "```bash",
                f"python3 one-tutor/scripts/study_loop.py {command}",
                "```",
                "",
                "```text",
                output,
                "```",
                "",
            ]
        )
    (RESULTS / "commands-and-output.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Demo results written to {RESULTS}")


if __name__ == "__main__":
    main()
