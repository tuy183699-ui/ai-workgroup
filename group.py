#!/usr/bin/env python3
"""AI workgroup v0.2: leader splits -> worker does -> leader reviews + budget.
Workers: mock (no key, default) / OpenAI-compatible API workers:
  deepseek / qwen / kimi(Moonshot) / zhipu(GLM)
Keys come from env vars only, never written to files:
  DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / MOONSHOT_API_KEY / ZHIPU_API_KEY
Usage: python3 group.py "task" [--worker deepseek]
"""
import argparse, json, os, sys, urllib.request
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
BUDGET_FILE = os.path.join(BASE, "budget.json")
DAILY_BUDGET_CNY = 10.0

PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek-1号", "base": "https://api.deepseek.com",
        "model": "deepseek-chat", "env": "DEEPSEEK_API_KEY",
        "price_in": 2.0 / 1e6, "price_out": 8.0 / 1e6,
    },
    "qwen": {
        "name": "通义千问-2号", "base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus", "env": "DASHSCOPE_API_KEY",
        "price_in": 0.8 / 1e6, "price_out": 2.0 / 1e6,
    },
    "kimi": {
        "name": "Kimi-3号", "base": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k", "env": "MOONSHOT_API_KEY",
        "price_in": 12.0 / 1e6, "price_out": 12.0 / 1e6,
    },
    "zhipu": {
        "name": "智谱GLM-4号", "base": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash", "env": "ZHIPU_API_KEY",
        "price_in": 0.0, "price_out": 0.0,
    },
}


def load_budget():
    today = date.today().isoformat()
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") == today:
            return data
    return {"date": today, "spent_cny": 0.0, "calls": 0}


def save_budget(b):
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(b, f, ensure_ascii=False, indent=2)


class MockWorker:
    name = "模拟组员-1号"
    cost_cny = 0.0

    def work(self, subtask):
        return "已完成子任务「" + subtask[:40] + "」: (模拟产出) 占位成果, 接入真 API Key 后这里会是组员的真实回答。"


class APIWorker:
    def __init__(self, provider):
        cfg = PROVIDERS[provider]
        self.cfg = cfg
        self.name = cfg["name"]
        self.key = os.environ.get(cfg["env"], "")
        if not self.key:
            raise SystemExit("未检测到 %s: 该组员还没拿到 Key, 先给它录入后再运行。" % cfg["env"])
        self.cost_cny = 0.0

    def work(self, subtask):
        body = json.dumps({
            "model": self.cfg["model"],
            "messages": [
                {"role": "system", "content": "你是 AI 工作群的组员 " + self.name + ", 只完成分到的子任务, 输出简洁, 给出可核查的结果。"},
                {"role": "user", "content": subtask},
            ],
        }).encode("utf-8")
        req = urllib.request.Request(
            self.cfg["base"] + "/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.key},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        u = data.get("usage", {})
        self.cost_cny += u.get("prompt_tokens", 0) * self.cfg["price_in"] + u.get("completion_tokens", 0) * self.cfg["price_out"]
        return data["choices"][0]["message"]["content"].strip()


def leader_split(task):
    return ["完成主任务: " + task, "检查上一步产出有没有跑题或缺漏, 列出问题(如无问题写'无')"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--worker", choices=["mock"] + list(PROVIDERS), default="mock")
    args = ap.parse_args()
    worker = MockWorker() if args.worker == "mock" else APIWorker(args.worker)
    budget = load_budget()
    print("【组长】收到任务: " + args.task)
    outputs = []
    for i, st in enumerate(leader_split(args.task), 1):
        prompt = st if i == 1 else st + "\n上一步产出: " + outputs[-1]
        print("【组长】派活 #%d -> %s: %s" % (i, worker.name, st))
        out = worker.work(prompt)
        outputs.append(out)
        print("【%s】交活 #%d: %s" % (worker.name, i, out))
    ok = all(o.strip() for o in outputs)
    print("【组长】" + ("验收通过: 产出完整" if ok else "验收未通过: 有空产出, 需返工"))
    if args.worker != "mock":
        budget["spent_cny"] = round(budget["spent_cny"] + worker.cost_cny, 4)
        budget["calls"] += len(outputs)
        save_budget(budget)
    print("【预算】今日 ¥%.2f / ¥%.0f (本轮组员成本约 ¥%.4f)" % (budget["spent_cny"], DAILY_BUDGET_CNY, worker.cost_cny))
    return 0


if __name__ == "__main__":
    sys.exit(main())
