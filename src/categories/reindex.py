#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild generated/index.json from generated metadata files."
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=Path("generated"),
        help="Root directory containing metadata and index outputs.",
    )
    return parser.parse_args()


def index_item_from_metadata(path: Path) -> dict[str, object]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    item: dict[str, object] = {
        "id": metadata["full_id"],
        "group_id": metadata["group_id"],
        "model_id": metadata["model_id"],
        "name": metadata["nice_name"],
        "description": metadata["description"],
    }
    if "dimensions_mm" in metadata:
        item["dimensions_mm"] = metadata["dimensions_mm"]
    if "dimensions_label" in metadata:
        item["dimensions_label"] = metadata["dimensions_label"]
    return item


def rebuild_index(generated_dir: Path) -> Path:
    metadata_dir = generated_dir / "metadata"
    metadata_paths = sorted(metadata_dir.rglob("*.json")) if metadata_dir.exists() else []
    models = sorted(
        (index_item_from_metadata(path) for path in metadata_paths),
        key=lambda item: str(item["id"]),
    )

    index_path = generated_dir / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "asset_layout": "flat",
                "models": models,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_csv(generated_dir / "index.csv", models)
    return index_path


def write_csv(path: Path, models: list[dict[str, object]]) -> None:
    fieldnames = [
        "id",
        "group_id",
        "model_id",
        "name",
        "description",
        "dimensions_x_mm",
        "dimensions_y_mm",
        "dimensions_z_mm",
        "dimensions_label",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for model in models:
            dimensions = model.get("dimensions_mm")
            dimensions = dimensions if isinstance(dimensions, dict) else {}
            writer.writerow(
                {
                    "id": model.get("id", ""),
                    "group_id": model.get("group_id", ""),
                    "model_id": model.get("model_id", ""),
                    "name": model.get("name", ""),
                    "description": model.get("description", ""),
                    "dimensions_x_mm": dimensions.get("x", ""),
                    "dimensions_y_mm": dimensions.get("y", ""),
                    "dimensions_z_mm": dimensions.get("z", ""),
                    "dimensions_label": model.get("dimensions_label", ""),
                }
            )


def main() -> int:
    args = parse_args()
    index_path = rebuild_index(args.generated_dir)
    print(index_path)
    print(args.generated_dir / "index.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
