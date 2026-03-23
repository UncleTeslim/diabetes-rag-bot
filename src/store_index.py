"""
src/store_index.py — Legacy index builder (kept for backward compatibility).

This module no longer runs automatically on import.
Use build_index.py at the project root instead:

  python build_index.py          # smart skip if already populated
  python build_index.py --force  # force full rebuild after adding PDFs
"""

import os
import sys


def main() -> None:
    # Ensure the project root (parent of src/) is on sys.path so that
    # build_index.py can be imported when this file is run directly.
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

    from build_index import build  # noqa: PLC0415

    build(force=True)


if __name__ == "__main__":
    main()
