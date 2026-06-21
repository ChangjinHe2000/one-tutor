import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "one-tutor" / "scripts" / "study_loop.py"
SPEC = importlib.util.spec_from_file_location("study_loop", SCRIPT)
study_loop = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(study_loop)


def question(question_id, topic, stem=None):
    return study_loop.canonicalize_question(
        {
            "id": question_id,
            "topic": topic,
            "type": "single_choice",
            "stem": stem or f"Question {question_id}?",
            "options": {"A": "Wrong", "B": "Right"},
            "answer": "B",
            "explanation": "B is correct.",
            "source": "test",
        }
    )


def history_row(question_id, topic, *, confidence, correct, next_review, session_id="s1"):
    row = {field: "" for field in study_loop.HISTORY_FIELDS}
    row.update(
        {
            "session_id": session_id,
            "session_date": "2026-06-01",
            "question_id": question_id,
            "topic": topic,
            "bucket": "review",
            "confidence": confidence,
            "is_correct": str(correct).lower(),
            "mastery": "needs-review" if not correct else "learning",
            "repetitions": "0" if not correct else "1",
            "interval_days": "1",
            "ease": "2.3",
            "next_review": next_review,
        }
    )
    return row


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "subject": "测试学科",
            "mix": {"new": 0.5, "review": 0.35, "weak": 0.15},
            "seed_salt": "test",
        }

    def test_auto_detects_chinese(self):
        self.assertEqual(study_loop.display_language(self.config), "zh")
        self.assertEqual(study_loop.display_language({"subject": "Biology"}), "en")

    def test_one_question_session_reserves_due_review(self):
        questions = [question("high-wrong", "A"), question("low-wrong", "B"), question("new", "C")]
        history = [
            history_row("high-wrong", "A", confidence="high", correct=False, next_review="2026-06-02"),
            history_row("low-wrong", "B", confidence="low", correct=False, next_review="2026-06-02"),
        ]
        selected = study_loop.select_questions(questions, history, self.config, "round-2", date(2026, 6, 2), 1)
        self.assertEqual(selected[0]["question"]["id"], "high-wrong")
        self.assertEqual(selected[0]["bucket"], "review")

    def test_weak_topics_keep_severity_order(self):
        questions = [question("weak-a", "Very weak"), question("weak-b", "Less weak")]
        history = [
            history_row("weak-a", "Very weak", confidence="low", correct=False, next_review="2026-07-01", session_id="a1"),
            history_row("weak-a", "Very weak", confidence="low", correct=False, next_review="2026-07-01", session_id="a2"),
            history_row("weak-b", "Less weak", confidence="low", correct=False, next_review="2026-07-01", session_id="b1"),
        ]
        config = {**self.config, "mix": {"new": 0, "review": 0, "weak": 1}}
        selected = study_loop.select_questions(questions, history, config, "weak-round", date(2026, 6, 2), 2)
        self.assertEqual([item["question"]["topic"] for item in selected], ["Very weak", "Less weak"])

    def test_repaired_excluded_question_returns_as_review(self):
        repaired = question("repaired", "A")
        excluded = {field: "" for field in study_loop.HISTORY_FIELDS}
        excluded.update(
            {
                "session_id": "old",
                "session_date": "2026-06-01",
                "question_id": "repaired",
                "topic": "A",
                "bucket": "new",
                "confidence": "medium",
                "error_type": "invalid-question",
                "mastery": "excluded",
            }
        )
        selected = study_loop.select_questions(
            [repaired], [excluded], self.config, "after-repair", date(2026, 6, 2), 1
        )
        self.assertEqual(selected[0]["question"]["id"], "repaired")
        self.assertEqual(selected[0]["bucket"], "review")


class CliWorkflowTests(unittest.TestCase):
    def run_cli(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            check=check,
            capture_output=True,
            text=True,
        )

    def test_chinese_workflow_disables_excluded_question(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "study"
            result = self.run_cli(
                "init",
                project,
                "--subject",
                "软件设计师考试",
                "--quiz-size",
                "2",
                "--language",
                "auto",
            )
            self.assertIn("学习项目已初始化", result.stdout)

            questions = [
                question("cn-1", "操作系统", "进程调度的目的是什么？"),
                question("cn-2", "数据库", "事务的原子性指什么？"),
                question("cn-3", "网络", "TCP 属于哪一层？"),
            ]
            study_loop.write_bank(project / "question-bank.jsonl", questions)
            result = self.run_cli(
                "generate", project, "--date", "2026-06-01", "--session", "round-1", "--size", "2"
            )
            self.assertIn("已生成 2 道题", result.stdout)
            quiz = (project / "sessions" / "round-1.md").read_text(encoding="utf-8")
            self.assertIn("自适应测验", quiz)
            self.assertIn("稳", quiz)

            session = json.loads((project / "sessions" / "round-1.json").read_text(encoding="utf-8"))
            excluded_id = session["questions"][0]["question_id"]
            answers = {
                "session_id": "round-1",
                "answers": [
                    {
                        "number": item["number"],
                        "answer": "" if index == 0 else "B",
                        "confidence": "稳",
                        "exclude": index == 0,
                        "notes": "题目有歧义" if index == 0 else "",
                    }
                    for index, item in enumerate(session["questions"])
                ],
            }
            answers_path = project / "sessions" / "round-1.answers.json"
            answers_path.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
            result = self.run_cli("grade", project, "--session", "round-1", "--answers", answers_path)
            self.assertIn("已批改 1 道题", result.stdout)
            feedback = (project / "feedback" / "round-1.md").read_text(encoding="utf-8")
            self.assertIn("答题反馈", feedback)
            self.assertIn("异常或排除题", feedback)

            bank = {item["id"]: item for item in study_loop.load_bank(project / "question-bank.jsonl")}
            self.assertEqual(bank[excluded_id]["status"], "disabled")

            self.run_cli(
                "generate", project, "--date", "2026-06-02", "--session", "round-2", "--size", "2"
            )
            next_session = json.loads((project / "sessions" / "round-2.json").read_text(encoding="utf-8"))
            self.assertNotIn(excluded_id, [item["question_id"] for item in next_session["questions"]])

            status = self.run_cli("status", project, "--date", "2026-06-02")
            self.assertIn("学科：软件设计师考试", status.stdout)
            self.assertIn("薄弱知识点", status.stdout)

            bank[excluded_id]["status"] = "active"
            study_loop.write_bank(project / "question-bank.jsonl", bank.values())
            repaired_status = self.run_cli("status", project, "--date", "2026-06-02")
            self.assertIn("到期 2 题", repaired_status.stdout)

    def test_feedback_puts_high_confidence_error_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "study"
            self.run_cli("init", project, "--subject", "测试", "--quiz-size", "2", "--language", "zh")
            questions = [question("low", "知识点一", "第一题？"), question("high", "知识点二", "第二题？")]
            study_loop.write_bank(project / "question-bank.jsonl", questions)
            study_loop.write_json(
                project / "sessions" / "priority.json",
                {
                    "session_id": "priority",
                    "date": "2026-06-01",
                    "subject": "测试",
                    "language": "zh",
                    "questions": [
                        {"number": 1, "question_id": "low", "bucket": "new"},
                        {"number": 2, "question_id": "high", "bucket": "new"},
                    ],
                },
            )
            answers_path = project / "sessions" / "priority.answers.json"
            study_loop.write_json(
                answers_path,
                {
                    "session_id": "priority",
                    "answers": [
                        {"number": 1, "answer": "A", "confidence": "蒙", "exclude": False},
                        {"number": 2, "answer": "A", "confidence": "稳", "exclude": False},
                    ],
                },
            )
            self.run_cli("grade", project, "--session", "priority", "--answers", answers_path)
            feedback = (project / "feedback" / "priority.md").read_text(encoding="utf-8")
            self.assertLess(feedback.index("### 第 2 题"), feedback.index("### 第 1 题"))
            self.assertIn("分类：概念误解", feedback)


if __name__ == "__main__":
    unittest.main()
