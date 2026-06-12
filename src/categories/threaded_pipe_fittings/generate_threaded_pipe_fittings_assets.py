#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_SRC = Path(__file__).resolve().parents[2]
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from categories.generate import main


if __name__ == "__main__":
    if not any(arg == "--only-category" or arg.startswith("--only-category=") for arg in sys.argv):
        sys.argv[1:1] = ["--only-category", "threaded_pipe_fittings"]
    raise SystemExit(main())
