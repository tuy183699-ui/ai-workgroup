# AI Workgroup · AI 工作群

A tiny multi-agent workgroup in pure Python (standard library only, no dependencies).
A **leader** splits a task into subtasks, dispatches them to **worker agents** backed by
different LLM providers, reviews the outputs, and tracks spending against a daily budget cap.

一个极简的多智能体协作命令行工具，纯 Python 标准库实现，零依赖。
**组长**负责拆分任务、派活和验收；**组员**是接入不同大模型厂商的 worker；
每次运行都会按 token 估算成本，并受每日预算上限约束。

## Features

- **Leader / worker orchestration** — the leader splits a task, a worker executes,
  and the follow-up subtask reviews the previous output for gaps or drift.
- **Multiple providers, one interface** — DeepSeek, Qwen (DashScope), Kimi (Moonshot)
  and Zhipu GLM, all through OpenAI-compatible chat-completions endpoints.
- **Budget guardrail** — per-provider token pricing, a daily spend cap (default ¥10/day),
  and a running ledger in `budget.json`.
- **Keys stay out of the code** — API keys are read from environment variables only,
  never written to files.
- **Mock worker** — runs with no key and no cost, so you can try the flow first.

## Quickstart

```bash
# Demo mode (no API key needed)
python3 group.py "Write a short product intro for a desk lamp"

# Real worker (example: DeepSeek)
export DEEPSEEK_API_KEY="your-key"
python3 group.py "Summarize this week's issues and draft a release note" --worker deepseek
```

## Providers

| Worker | Model | API key env var |
| --- | --- | --- |
| `deepseek` | `deepseek-chat` | `DEEPSEEK_API_KEY` |
| `qwen` | `qwen-plus` | `DASHSCOPE_API_KEY` |
| `kimi` | `moonshot-v1-8k` | `MOONSHOT_API_KEY` |
| `zhipu` | `glm-4-flash` | `ZHIPU_API_KEY` |
| `mock` (default) | — | — |

## How it works

1. The leader turns your task into two subtasks: *do it*, then *review the result*.
2. The selected worker answers each subtask in sequence (the review sees the first output).
3. The leader accepts or rejects the result and prints the updated daily budget.

## Status & roadmap

Early-stage personal project (v0.2), maintained by one person. Working today:
dispatch → execute → review → budget ledger, with four providers wired up.
Planned next: parallel workers, more providers, and a chat-style web UI.

## License

MIT — see [LICENSE](LICENSE).
