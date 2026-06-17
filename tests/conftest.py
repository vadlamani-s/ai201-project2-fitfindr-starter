from pathlib import Path
import sys

# Ensure the repository root is on sys.path so tests can import top-level modules.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
