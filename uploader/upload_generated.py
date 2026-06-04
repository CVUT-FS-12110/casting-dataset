from __future__ import annotations

import argparse
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENERATED_DIR = PROJECT_ROOT / "generated"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class UploadItem:
    source: Path
    key: str


@dataclass(frozen=True)
class S3Config:
    bucket: str
    endpoint_url: str | None
    access_key: str
    secret_key: str
    region: str | None = None


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def config_from_env(path: Path) -> S3Config:
    env_file = parse_env(path)

    def setting(*names: str) -> str | None:
        for name in names:
            value = os.environ.get(name) or env_file.get(name)
            if value:
                return value
        return None

    bucket = setting("BUCKET", "S3_BUCKET", "AWS_BUCKET")
    access_key = setting("ACCESS_KEY", "AWS_ACCESS_KEY_ID")
    secret_key = setting("SECRET_KEY", "AWS_SECRET_ACCESS_KEY")
    endpoint_url = setting("ENDPOINT", "S3_ENDPOINT", "AWS_ENDPOINT_URL")
    region = setting("REGION", "AWS_DEFAULT_REGION")

    missing = [
        label
        for label, value in (
            ("BUCKET", bucket),
            ("ACCESS_KEY", access_key),
            ("SECRET_KEY", secret_key),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required S3 setting(s): {joined}")

    return S3Config(
        bucket=bucket,
        endpoint_url=endpoint_url,
        access_key=access_key,
        secret_key=secret_key,
        region=region,
    )


def upload_items(generated_dir: Path) -> list[UploadItem]:
    folders = {
        "metadata": generated_dir / "metadata",
        "mesh": generated_dir / "mesh",
        "sections": generated_dir / "sections",
        "step": generated_dir / "step",
    }
    items = [
        UploadItem(generated_dir / "index.json", "index.json"),
        UploadItem(generated_dir / "index.csv", "index.csv"),
    ]

    for key_folder, source_folder in folders.items():
        if not source_folder.exists():
            continue
        for source in sorted(path for path in source_folder.rglob("*") if path.is_file()):
            items.append(UploadItem(source, f"{key_folder}/{source.name}"))
    return items


def content_type(path: Path) -> str:
    if path.suffix.lower() == ".glb":
        return "model/gltf-binary"
    if path.suffix.lower() in {".step", ".stp"}:
        return "model/step"
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def build_client(config: S3Config):
    try:
        import boto3
    except ImportError as exc:
        raise SystemExit("Missing dependency: install boto3 before uploading.") from exc

    return boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key,
        aws_secret_access_key=config.secret_key,
        region_name=config.region,
    )


def configure_bucket_cors(client, bucket: str, *, dry_run: bool) -> None:
    cors = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "HEAD"],
                "AllowedOrigins": ["*"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
    print(f"{'DRY ' if dry_run else ''}CONFIGURE CORS s3://{bucket} (GET, HEAD from any origin)")
    if not dry_run:
        try:
            client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors)
        except Exception:
            cors["CORSRules"][0].pop("ExposeHeaders", None)
            client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors)


def upload(
    items: list[UploadItem],
    config: S3Config,
    *,
    dry_run: bool,
    cache_control: str | None,
) -> None:
    client = None if dry_run else build_client(config)
    configure_bucket_cors(client, config.bucket, dry_run=dry_run)
    for item in items:
        if not item.source.exists():
            if item.key == "index.csv":
                continue
            raise SystemExit(f"Missing source file: {item.source}")

        extra_args = {
            "ContentType": content_type(item.source),
            "ACL": "public-read",
        }
        if cache_control:
            extra_args["CacheControl"] = cache_control

        size = item.source.stat().st_size
        print(
            f"{'DRY ' if dry_run else ''}UPLOAD {item.source} -> "
            f"s3://{config.bucket}/{item.key} ({size} bytes, public-read)"
        )
        if client is not None:
            client.upload_file(
                str(item.source),
                config.bucket,
                item.key,
                ExtraArgs=extra_args,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload generated flat browser assets to an S3-compatible bucket."
    )
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument("--generated-dir", type=Path, default=DEFAULT_GENERATED_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Print upload plan without sending files.")
    parser.add_argument(
        "--cache-control",
        default="public, max-age=3600",
        help="Cache-Control header for uploaded objects. Use an empty string to omit it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = config_from_env(args.env_file)
    cache_control = args.cache_control or None
    items = upload_items(args.generated_dir)
    if not items:
        raise SystemExit("No generated assets found to upload.")
    upload(
        items,
        config,
        dry_run=args.dry_run,
        cache_control=cache_control,
    )
    print(f"Uploaded {len(items)} object(s)." if not args.dry_run else f"Planned {len(items)} object(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
