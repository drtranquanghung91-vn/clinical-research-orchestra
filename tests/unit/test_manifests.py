import json
import unittest

import _paths  # noqa: F401
from _paths import ROOT


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


class TestManifests(unittest.TestCase):
    def test_marketplace_lists_both_plugins_with_existing_sources(self):
        m = load(".claude-plugin/marketplace.json")
        self.assertEqual(m["name"], "clinical-research-orchestra")
        names = [p["name"] for p in m["plugins"]]
        self.assertEqual(sorted(names), ["orchestra", "phi-guard"])
        for p in m["plugins"]:
            self.assertTrue((ROOT / p["source"]).is_dir(), p["source"])

    def test_plugin_names_and_versions_match_marketplace(self):
        m = load(".claude-plugin/marketplace.json")
        version = m["metadata"]["version"]
        for p in m["plugins"]:
            pj = load(f"{p['source']}/.claude-plugin/plugin.json")
            self.assertEqual(pj["name"], p["name"])
            self.assertEqual(pj["version"], version)
            self.assertEqual(pj["license"], "MIT")
            self.assertEqual(pj["author"]["name"], "Trần Quang Hưng")

    def test_required_root_files_exist(self):
        for f in ["LICENSE", "README.md", "NOTICE.md", "CONTRIBUTORS.md", "CHANGELOG.md", "AGENTS.md", "CLAUDE.md"]:
            self.assertTrue((ROOT / f).is_file(), f)
        self.assertIn("Amelia Le", (ROOT / "CONTRIBUTORS.md").read_text(encoding="utf-8"))

    def test_orchestra_gate_hook_registered(self):
        hj = load("plugins/orchestra/hooks/hooks.json")
        entry = hj["hooks"]["PreToolUse"][0]
        self.assertEqual(set(entry["matcher"].split("|")), {"Bash", "PowerShell", "Agent", "Task"})
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/gate_hook.py", entry["hooks"][0]["command"])
        self.assertTrue((ROOT / "plugins" / "orchestra" / "scripts" / "gate_hook.py").is_file())

    def test_codex_and_antigravity_manifests(self):
        m = load(".claude-plugin/marketplace.json")
        version = m["metadata"]["version"]
        for p in m["plugins"]:
            claude = load(f"{p['source']}/.claude-plugin/plugin.json")
            for host in (".codex-plugin", ".antigravity-plugin"):
                with self.subTest(plugin=p["name"], host=host):
                    pj = load(f"{p['source']}/{host}/plugin.json")
                    self.assertEqual(pj["name"], p["name"])
                    self.assertEqual(pj["version"], version)
                    self.assertEqual(pj["license"], "MIT")
                    self.assertEqual(pj["author"]["name"], "Trần Quang Hưng")
                    self.assertEqual(pj["repository"], claude["repository"])
                    self.assertTrue(pj["description"])
                    self.assertNotIn("logo", pj)
            codex = load(f"{p['source']}/.codex-plugin/plugin.json")
            self.assertEqual(codex["skills"], "./skills/")
            self.assertTrue((ROOT / p["source"] / "skills").is_dir())
            self.assertEqual(codex["interface"]["developerName"], "Trần Quang Hưng")
            self.assertNotIn("logo", codex["interface"])
            self.assertTrue(load(f"{p['source']}/.antigravity-plugin/plugin.json")["displayName"])

    def test_readme_other_hosts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for s in ("### Other hosts (Codex, Antigravity)", "$env:CLAUDE_PLUGIN_ROOT", "set CLAUDE_PLUGIN_ROOT=",
                  'export CLAUDE_PLUGIN_ROOT="<repo>/plugins/orchestra"', "not automatic"):
            self.assertIn(s, readme)


if __name__ == "__main__":
    unittest.main()
