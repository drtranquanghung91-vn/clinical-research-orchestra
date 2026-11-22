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


if __name__ == "__main__":
    unittest.main()
