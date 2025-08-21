"""Hello world example for symphonia.

This script demonstrates the intended API and writes a placeholder JSON file.
"""

import json
from pathlib import Path


def main() -> None:  # pragma: no cover - stub
    """Run the hello world example."""
    data = {"triples": [["A", "rel", "B"], ["C", "rel", "D"]]}
    out_path = Path(__file__).parent / "kg.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"✅ Wrote {len(data['triples'])} triples to {out_path}")


if __name__ == "__main__":
    main()
