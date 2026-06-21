<h1 align="center">OneTutor</h1>

<h3 align="center">你的私人 AI 学习教练</h3>

<p align="center">
  <strong>一个可安装到 Codex 的自适应学习 Skill</strong>
</p>

<p align="center">
  <a href="https://github.com/ChangjinHe2000/one-tutor/stargazers"><img src="https://img.shields.io/github/stars/ChangjinHe2000/one-tutor?style=flat-square&logo=github&label=Stars" alt="GitHub Stars"></a>
  <a href="https://github.com/ChangjinHe2000/one-tutor/forks"><img src="https://img.shields.io/github/forks/ChangjinHe2000/one-tutor?style=flat-square&logo=github&label=Forks" alt="GitHub Forks"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/ChangjinHe2000/one-tutor?style=flat-square&label=License" alt="MIT License"></a>
  <a href="one-tutor/SKILL.md"><img src="https://img.shields.io/badge/Codex-Skill-10A37F?style=flat-square" alt="Codex Skill"></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/ChangjinHe2000/one-tutor/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/ChangjinHe2000/one-tutor/test.yml?branch=main&style=flat-square&label=Tests" alt="Tests"></a>
</p>

<p align="center">
  <a href="#quick-start">🚀 快速开始</a>
  &nbsp;·&nbsp;
  <a href="one-tutor/SKILL.md">🧩 Skill 定义</a>
  &nbsp;·&nbsp;
  <a href="#how-it-works">🧠 工作原理</a>
  &nbsp;·&nbsp;
  <a href="#soft-exam-demo">👀 软考实测</a>
  &nbsp;·&nbsp;
  <a href="#privacy">🔒 数据与隐私</a>
</p>

<p align="center">
  <a href="assets/one-tutor-overview.jpg">
    <img src="assets/one-tutor-overview.jpg" alt="OneTutor 功能概览：资料建库、自适应出题、信心作答、错因诊断和间隔复习" width="100%">
  </a>
</p>

---

> [!TIP]
> **把任何学习资料变成你的私人课程。**
>
> OneTutor 可以把笔记、教材、PDF、DOCX、课程资料或现有题库，变成一套会持续了解你的学习系统：自动出题、收集答案与信心程度、分析错误、识别薄弱知识点，并安排下一次复习。

**OneTutor 是一个开源 Codex Skill，不是预置题库，也不是独立的在线课程平台。**

> 一位学习者，一位专属导师，任何学科。

## ✨ 这是一个什么 Skill？

安装 OneTutor 后，你可以直接让 Codex：

- 根据自己的学习资料建立可追溯的题库
- 自动组合新题、到期复习题和薄弱知识点强化题
- 同时记录答案正确性与“稳 / 不确定 / 蒙”的信心程度
- 区分知识缺口、概念误解、蒙对和题目本身异常
- 根据作答表现安排间隔复习
- 生成错题反馈、章节表现和掌握度报告
- 为任意学科建立每日自动出题与复习流程

<a id="how-it-works"></a>

## 🧠 工作原理

普通提示词通常只完成一次出题。OneTutor 把完整学习闭环固化为可复用能力：

```text
你的学习资料
    ↓
基于原文建立题库
    ↓
新题 + 到期复习 + 薄弱点强化
    ↓
作答 + 信心标记
    ↓
批改 + 错因诊断
    ↓
安排下一次复习
```

Codex 负责理解资料、编写题目和提供个性化讲解；Skill 自带的确定性脚本负责题库校验、选题、批改、学习记录与间隔复习调度。

<a id="soft-exam-demo"></a>

## 👀 用软考题目跑一次真实闭环

仓库内置了一套由真实软考复习记录中的薄弱点改写而成的公开示例。下面的数据不是宣传文案，而是 OneTutor 脚本的真实运行结果：

| 阶段 | OneTutor 的处理结果 |
| --- | --- |
| 第一轮出题 | 从 10 道题中生成 6 道新题 |
| 模拟作答 | 5/6，包含“稳但答错”“蒙对”“不确定但答对” |
| 错因诊断 | 概念误解 1 题、蒙对 1 题、答对但不确定 1 题 |
| 次日状态 | 6 道题到期，薄弱点为 UML、信息安全、软件工程 |
| 第二轮出题 | 自动组合 2 道复习题 + 1 道薄弱点强化题 + 3 道新题 |

<p align="center">
  <a href="assets/soft-exam-feedback.png">
    <img src="assets/soft-exam-feedback.png" alt="OneTutor 软考实测答题反馈：得分、信心程度、错因分类、解析与下次复习时间" width="760">
  </a>
</p>

<p align="center"><sub>由 OneTutor 真实生成的第一轮软考答题反馈，不是手工制作的效果图。</sub></p>

这张反馈图体现了 OneTutor 与普通判分工具的区别：**5/6 并不等于其余知识都已掌握**。

- **稳但答错 → 概念误解**：第 1 题被放在最前面优先复习，因为错误来自较稳定但不正确的认知。
- **蒙但答对 → 蒙对**：第 2 题虽然得分，但仍会进入近期复习，避免一次偶然正确被误判为掌握。
- **不确定但答对 → 继续巩固**：第 3 题保留正确记录，同时缩短复习间隔。
- **反馈可以继续驱动下一轮**：每道重点题都带有正确答案、解析、错因和下次复习日期；这些记录会参与后续 `review` 与 `weak` 选题。

可以直接查看：

- [完整软考实测说明](examples/soft-exam/README.md)
- [第一轮测验](examples/soft-exam/results/01-round-1-quiz.md)
- [批改与错因诊断](examples/soft-exam/results/03-round-1-feedback.md)
- [第二轮自适应测验](examples/soft-exam/results/04-round-2-quiz.md)
- [可复现的命令与真实输出](examples/soft-exam/results/commands-and-output.md)

一条命令即可重新生成全部展示结果：

```bash
python3 examples/soft-exam/run_demo.py
```

<a id="requirements"></a>

## 📦 安装要求

- 支持 Skills 的 Codex
- Python 3.10 或更高版本
- 不需要安装任何第三方 Python 包

<a id="quick-start"></a>

## 🚀 快速开始

### 1. 安装 Skill

克隆仓库，并把 `one-tutor` Skill 复制到 Codex Skills 目录：

```bash
git clone https://github.com/ChangjinHe2000/one-tutor.git
mkdir -p ~/.codex/skills
cp -R one-tutor/one-tutor ~/.codex/skills/one-tutor
```

如果没有立即显示该 Skill，请重新启动 Codex。

### 2. 交给你的私人导师

安装后可以这样对 Codex 说：

```text
使用 $one-tutor，把这些学习资料变成每天自动出题和复习的自适应学习流程。
```

或者：

```text
使用 $one-tutor，根据这份 PDF 考我；批改时记录我的信心程度，并安排薄弱知识点复习。
```

还可以直接查询进度：

```text
使用 $one-tutor，告诉我今天有哪些内容需要复习，以及目前最薄弱的三个知识点。
```

## 📝 支持的题型

- 单项选择题
- 多项选择题
- 判断题
- 简答题
- 需要 Codex 语义判断的人工批改题

<a id="privacy"></a>

## 🔒 数据与隐私

- 学习资料、题库、作答历史和复习记录默认保存在本地
- Skill 本身不包含教材、付费课程、个人笔记或私人学习记录
- 学习项目与 Skill 安装目录相互独立，更新 Skill 不会覆盖学习记录
- 请只使用自己有权使用的学习资料

## 🧪 本地验证

仓库的回归测试覆盖中文学习闭环、复习优先级、异常题排除和修复后的重新启用：

```bash
python3 -m unittest discover -s tests -v
```

测试仅使用 Python 标准库；推送到 GitHub 后也会由 GitHub Actions 自动运行。

## 📄 开源协议

[MIT License](LICENSE)
