"""Summarise a `claude -p --output-format stream-json --verbose` transcript.

Usage: python tests/scenarios/summarize_run.py run.jsonl
Prints the init event (plugins, MCP servers, tools), every tool call with its
input, every hook/permission denial text seen, and the final result.
"""
import json
import sys


def main(path):
    sys.stdout.reconfigure(encoding="utf-8")
    calls, denials, result = [], [], ""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            ev = json.loads(line)
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                print("INIT plugins:", [p.get("name") for p in ev.get("plugins", [])])
                print("INIT mcp_servers:", ev.get("mcp_servers"))
                print("INIT skills:", ev.get("skills"))
                print("INIT memory_paths:", ev.get("memory_paths"))
            msg = ev.get("message")
            if not isinstance(msg, dict):
                msg = {}
            content = msg.get("content")
            if not isinstance(content, list):
                content = []
            for block in content:
                if block.get("type") == "tool_use":
                    calls.append((block.get("name"), json.dumps(block.get("input"), ensure_ascii=False)))
                if block.get("type") == "tool_result":
                    text = json.dumps(block.get("content"), ensure_ascii=False)
                    if "phi-guard" in text or "denied" in text.lower() or "permission" in text.lower():
                        denials.append(text[:400])
            if ev.get("type") == "result":
                result = ev.get("result", "")
    print("TOOL CALLS:")
    for name, inp in calls:
        print(" -", name, inp[:300])
    print("DENIALS/PERMISSION RESULTS:")
    for d in denials:
        print(" -", d)
    print("RESULT:", result[:800])


if __name__ == "__main__":
    main(sys.argv[1])
