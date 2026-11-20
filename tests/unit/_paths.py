"""Put the plugin script folders on sys.path for tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH_SCRIPTS = ROOT / "plugins" / "orchestra" / "scripts"
PHI_SCRIPTS = ROOT / "plugins" / "phi-guard" / "scripts"
TOOLS = ROOT / "tools"
for p in (ORCH_SCRIPTS, PHI_SCRIPTS, TOOLS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
