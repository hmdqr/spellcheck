import re
import sys
from pathlib import Path


def bump(version: str) -> None:
    p = Path(__file__).resolve().parents[1] / "buildVars.py"
    text = p.read_text(encoding="utf-8")
    new = re.sub(r'("addon_version"\s*:\s*")(.*?)(")', rf'\1{version}\3', text)
    if text == new:
        print("No change needed (same version).")
    p.write_text(new, encoding="utf-8")
    print(f"Updated addon_version to {version} in {p}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/bump_version.py 1.3.1")
        sys.exit(1)
    bump(sys.argv[1])
