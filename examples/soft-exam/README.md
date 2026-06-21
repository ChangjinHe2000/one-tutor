# OneTutor 软考实测

这是一套由真实软考复习记录中的薄弱点改写而成的公开演示。它不复制整套真题，也不包含用户的私人作答历史或本机绝对路径。

## 可以怎样使用

自然语言方式：

```text
使用 $one-tutor，把这份软考题库做成每天 6 题的自适应复习。
```

```text
使用 $one-tutor，根据我的作答和“稳 / 不确定 / 蒙”进行批改，先讲我有把握却答错的题。
```

```text
使用 $one-tutor，生成第二轮测验，混合新题、到期复习题和薄弱知识点强化题。
```

也可以直接运行 Skill 自带的零依赖 CLI：

```bash
python3 one-tutor/scripts/study_loop.py init /tmp/one-tutor-soft-exam \
  --subject "软件设计师考试" --quiz-size 6 --language zh

python3 one-tutor/scripts/study_loop.py import /tmp/one-tutor-soft-exam \
  --input examples/soft-exam/question-bank.jsonl --replace

python3 one-tutor/scripts/study_loop.py generate /tmp/one-tutor-soft-exam \
  --date 2026-06-01 --session round-1 --size 6
```

## 能看到什么结果

本演示故意安排了三种典型表现：

- 第 1 题“稳但答错”：识别为概念误解，反馈时优先展示。
- 第 2 题“蒙但答对”：识别为蒙对，不会因为偶然正确就判定掌握。
- 第 3 题“不确定但答对”：进入巩固状态，并安排近期复习。

真实运行产物：

- [第一轮测验](results/01-round-1-quiz.md)
- [模拟作答](results/02-round-1-answers.json)
- [批改与错因诊断](results/03-round-1-feedback.md)
- [下一日状态](results/status.txt)
- [第二轮自适应测验](results/04-round-2-quiz.md)
- [第二轮选题来源](results/05-round-2-session.json)
- [完整命令与终端输出](results/commands-and-output.md)

第二轮的 `session.json` 会直接标记每道题来自 `new`、`review`、`weak` 或 `fill`，便于验证自适应选题是否按预期工作。

## 重新生成展示结果

```bash
python3 examples/soft-exam/run_demo.py
```

脚本只依赖 Python 标准库，并在临时目录中完成初始化、导入、出题、批改、状态查询和第二轮出题。
