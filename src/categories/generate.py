#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO_SRC = Path(__file__).resolve().parents[1]
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from casting_dataset.assets import export_glb, export_section_pngs, measured_dimensions
from casting_dataset.brake_discs import (
    BrakeDiscSpec,
    brake_disc_index_item,
    brake_disc_metadata,
    brake_disc_presets,
    make_brake_disc,
)
from casting_dataset.step import export_step
from categories.reindex import rebuild_index


@dataclass(frozen=True)
class Category:
    group_id: str
    slug: str
    presets: Callable[[], dict[str, BrakeDiscSpec]]
    make_model: Callable[[BrakeDiscSpec], object]
    metadata: Callable[[BrakeDiscSpec, dict[str, float] | None], dict[str, object]]
    index_item: Callable[[BrakeDiscSpec, dict[str, float] | None], dict[str, object]]


CATEGORIES = {
    "001": Category(
        group_id="001",
        slug="brake_discs",
        presets=brake_disc_presets,
        make_model=make_brake_disc,
        metadata=brake_disc_metadata,
        index_item=brake_disc_index_item,
    )
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate casting dataset assets.")
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=Path("generated"),
        help="Root directory for generated outputs.",
    )
    parser.add_argument(
        "--only-steps",
        action="store_true",
        help="Generate STEP and metadata/index only; skip GLB meshes and section images.",
    )
    parser.add_argument(
        "--only-category",
        nargs="+",
        choices=sorted(CATEGORIES),
        help="Generate only selected category IDs, for example 001.",
    )
    parser.add_argument(
        "--only-model",
        nargs="+",
        help="Generate only selected model IDs, for example 001-003.",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip rebuilding generated/index.json after generation.",
    )
    return parser.parse_args()


def selected_categories(args: argparse.Namespace) -> list[Category]:
    category_ids = args.only_category or sorted(CATEGORIES)
    return [CATEGORIES[category_id] for category_id in category_ids]


def selected_specs(category: Category, args: argparse.Namespace) -> list[BrakeDiscSpec]:
    specs = list(category.presets().values())
    if not args.only_model:
        return specs

    requested = set(args.only_model)
    return [
        spec
        for spec in specs
        if spec.dataset_id in requested
    ]


def write_json(path: Path, data: object) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def output_paths(generated_dir: Path, category: Category, model_id: str) -> dict[str, Path]:
    return {
        "step": generated_dir / "step" / category.slug / f"{model_id}.step",
        "mesh": generated_dir / "mesh" / category.slug / f"{model_id}.glb",
        "metadata": generated_dir / "metadata" / category.slug / f"{model_id}.json",
        "sections": generated_dir / "sections" / category.slug,
    }


def generate_model(category: Category, spec: BrakeDiscSpec, args: argparse.Namespace) -> dict[str, float] | None:
    paths = output_paths(args.generated_dir, category, spec.dataset_id)
    model = category.make_model(spec)
    step_path = export_step(
        model,
        paths["step"],
        dataset_id=spec.dataset_id,
        display_name=spec.display_name,
        description=spec.description,
    )
    print(step_path)

    if not args.only_steps:
        glb_path = export_glb(step_path, paths["mesh"])
        print(glb_path)
        for section_path in export_section_pngs(glb_path, paths["sections"], spec.dataset_id):
            print(section_path)

    dimensions_mm = measured_dimensions(paths["mesh"])
    write_json(paths["metadata"], category.metadata(spec, dimensions_mm))
    print(paths["metadata"])
    return dimensions_mm


def main() -> int:
    args = parse_args()
    generated_count = 0

    for category in selected_categories(args):
        specs = selected_specs(category, args)
        for spec in specs:
            generate_model(category, spec, args)
            generated_count += 1

    if not generated_count:
        requested = ", ".join(args.only_model or args.only_category or ["<all>"])
        raise SystemExit(f"No models selected: {requested}")

    if not args.no_index:
        print(rebuild_index(args.generated_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
