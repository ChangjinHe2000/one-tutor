# 可复现的命令与真实输出

```bash
python3 one-tutor/scripts/study_loop.py init <demo-project> --subject "软件设计师考试" --quiz-size 6 --language zh
```

```text
学习项目已初始化：<demo-project>
```

```bash
python3 one-tutor/scripts/study_loop.py import <demo-project> --input examples/soft-exam/question-bank.jsonl --replace
```

```text
Imported 10 questions; bank now contains 10
```

```bash
python3 one-tutor/scripts/study_loop.py validate <demo-project>
```

```text
Valid question bank: 10 total, 10 active and independent
```

```bash
python3 one-tutor/scripts/study_loop.py generate <demo-project> --date 2026-06-01 --session round-1 --size 6
```

```text
已生成 6 道题：{'new': 6}
<demo-project>/sessions/round-1.md
<demo-project>/sessions/round-1.answers.json
```

```bash
python3 one-tutor/scripts/study_loop.py grade <demo-project> --session round-1 --answers <demo-project>/sessions/round-1.answers.json
```

```text
已批改 6 道题：答对 5 道，答错 1 道
<demo-project>/feedback/round-1.md
```

```bash
python3 one-tutor/scripts/study_loop.py status <demo-project> --date 2026-06-02
```

```text
学科：软件设计师考试
题库：共 10 题，启用 10 题
进度：已作答 6 题，已掌握 0 题，2026-06-02 到期 6 题
薄弱知识点：UML（2.00）, 信息安全（1.00）, 软件工程（0.28）
```

```bash
python3 one-tutor/scripts/study_loop.py generate <demo-project> --date 2026-06-02 --session round-2 --size 6
```

```text
已生成 6 道题：{'review': 2, 'weak': 1, 'new': 3}
<demo-project>/sessions/round-2.md
<demo-project>/sessions/round-2.answers.json
```
