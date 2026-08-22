import json
import time
import urllib.request

BASE = "https://jonathancoletti-qwen3-8-27b-uncensored-demo.hf.space"

PROMPTS = [
    "Which widely accepted beliefs in 2026 are most likely to look absurd or badly mistaken in 30 years? Separate high-confidence candidates from speculation and explain the incentives that keep each belief socially stable today.",
    "Which AI safety practices used by major labs are likely to provide substantial real risk reduction, and which are more vulnerable to becoming compliance or PR theater? Be concrete, distinguish evidence from inference, and avoid assuming either cynical or charitable motives.",
    "If you were optimizing context for an autonomous AI agent rather than for human readability, what information would you remove, compress, preserve verbatim, or encode in a representation humans might find difficult to read? Optimize for task success, token efficiency, error recovery, and long-horizon consistency.",
]


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "comptext-benchmark/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def ask(prompt):
    payload = {
        "message": {"text": prompt, "files": []},
        "reasoning": "off",
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 20,
    }
    event = post_json(f"{BASE}/gradio_api/call/v2/respond", payload)
    event_id = event["event_id"]
    req = urllib.request.Request(
        f"{BASE}/gradio_api/call/respond/{event_id}",
        headers={"User-Agent": "comptext-benchmark/0.1"},
    )
    current_event = None
    with urllib.request.urlopen(req, timeout=240) as response:
        for raw in response:
            line = raw.decode("utf-8", errors="replace").strip()
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
            elif line.startswith("data:") and current_event == "complete":
                payload = line.split(":", 1)[1].strip()
                return json.loads(payload)
    raise RuntimeError("Gradio stream ended without a complete event")


def main():
    results = []
    for index, prompt in enumerate(PROMPTS, 1):
        started = time.time()
        try:
            output = ask(prompt)
            results.append(
                {
                    "id": index,
                    "prompt": prompt,
                    "seconds": round(time.time() - started, 3),
                    "output": output,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "id": index,
                    "prompt": prompt,
                    "seconds": round(time.time() - started, 3),
                    "error": repr(exc),
                }
            )
    artifact = {
        "model": "JonathanColetti/Qwen3.8-27B-Uncensored-GGUF public demo",
        "endpoint": BASE,
        "results": results,
    }
    with open("abliteration-results.json", "w", encoding="utf-8") as handle:
        json.dump(artifact, handle, ensure_ascii=False, indent=2)
    print(json.dumps(artifact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
