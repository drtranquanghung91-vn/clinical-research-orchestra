import sys
from pathlib import Path
for _stream in (sys.stdout, sys.stderr):  # analysis output is UTF-8 (Windows consoles default to cp1252)
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass
sys.path.insert(0, str(Path(__file__).resolve().parent))
import crostats

df = crostats.load_data("04_data/cohort.deid.csv")
a = crostats.audit(df)
print(f"rows {a['rows']}  duplicate rows {a['duplicates']}")
print("variable | missing | outliers (IQR x 1.5)")
for col, miss in a["missing"].items():
    print(f"{col} | {miss} | {a['outliers'].get(col, '')}")
