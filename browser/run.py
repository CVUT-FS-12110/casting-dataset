from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the generated model browser.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9010)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument(
        "--bucket-url",
        help="Remote bucket base URL for real mode, for example https://bucket.example.com",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.bucket_url:
        os.environ["CASTING_DATA_BUCKET_URL"] = args.bucket_url.rstrip("/")
    uvicorn.run("browser.app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
