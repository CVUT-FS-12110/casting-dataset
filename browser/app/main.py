from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "docs"
BROWSER_STATIC_DIR = DOCS_DIR / "browser"
BROWSER_STATIC_ASSET_DIR = BROWSER_STATIC_DIR / "static"
GENERATED_DIR = PROJECT_ROOT / "generated"

app = FastAPI(title="Generated Model Browser")
app.mount(
    "/browser/static",
    StaticFiles(directory=BROWSER_STATIC_ASSET_DIR, check_dir=False),
    name="browser-static",
)


def flat_generated_path(key: str) -> Path:
    clean_key = Path(key)
    if clean_key.is_absolute() or ".." in clean_key.parts:
        raise HTTPException(status_code=404, detail="Asset not found")

    parts = clean_key.parts
    if parts == ("index.json",):
        return generated_dir() / "index.json"
    if len(parts) != 2:
        raise HTTPException(status_code=404, detail="Asset not found")

    folder, filename = parts
    if folder in {"metadata", "mesh", "sections", "step"}:
        return find_generated_asset(generated_dir() / folder, filename)

    raise HTTPException(status_code=404, detail="Asset not found")


def find_generated_asset(root: Path, filename: str) -> Path:
    if not root.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    direct = root / filename
    if direct.is_file():
        return direct
    matches = sorted(root.glob(f"*/{filename}"))
    if matches:
        return matches[0]
    raise HTTPException(status_code=404, detail="Asset not found")


def generated_dir() -> Path:
    configured = os.environ.get("CASTING_DATA_GENERATED_DIR")
    if configured:
        return Path(configured)
    return GENERATED_DIR


def file_response(path: Path) -> FileResponse:
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type, _ = mimetypes.guess_type(path.name)
    return FileResponse(path, media_type=media_type)


def clean_asset_key(key: str) -> str:
    clean_key = Path(key)
    if clean_key.is_absolute() or ".." in clean_key.parts:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not clean_key.parts:
        raise HTTPException(status_code=404, detail="Asset not found")
    return clean_key.as_posix()


def remote_bucket_url() -> str:
    url = os.environ.get("CASTING_DATA_BUCKET_URL")
    if not url:
        raise HTTPException(status_code=404, detail="Remote bucket URL is not configured")
    return url.rstrip("/")


@app.get("/")
def index_page():
    return file_response(DOCS_DIR / "index.html")


@app.get("/browser/")
def browser_index_page():
    return file_response(BROWSER_STATIC_DIR / "index.html")


@app.get("/index.html")
def index_html():
    return file_response(DOCS_DIR / "index.html")


@app.get("/model.html")
def model_html():
    return file_response(BROWSER_STATIC_DIR / "model.html")


@app.get("/browser/model.html")
def browser_model_html():
    return file_response(BROWSER_STATIC_DIR / "model.html")


@app.get("/models/{catalog_id}")
def model_page(catalog_id: str):
    return file_response(BROWSER_STATIC_DIR / "model.html")


@app.get("/config.json")
def config():
    return browser_config()


@app.get("/browser/config.json")
def browser_config():
    remote_url = os.environ.get("CASTING_DATA_BUCKET_URL")
    if remote_url:
        return {
            "assetBaseUrl": "/remote-generated",
            "remoteAssetBaseUrl": remote_url.rstrip("/"),
            "mode": "remote-proxy",
        }
    return {
        "assetBaseUrl": "/generated",
        "mode": os.environ.get("CASTING_DATA_BROWSER_MODE", "local"),
    }


@app.get("/generated/{key:path}")
def generated_asset(key: str):
    return file_response(flat_generated_path(key))


@app.get("/remote-generated/{key:path}")
def remote_generated_asset(key: str):
    clean_key = clean_asset_key(key)
    url = f"{remote_bucket_url()}/{quote(clean_key, safe='/')}"
    try:
        with urlopen(Request(url, method="GET"), timeout=60) as remote:
            data = remote.read()
            media_type = remote.headers.get("content-type") or content_type_from_key(clean_key)
            return Response(
                content=data,
                media_type=media_type,
                headers={"Cache-Control": "public, max-age=3600"},
            )
    except HTTPError as exc:
        raise HTTPException(status_code=exc.code, detail=f"Remote asset not available: {clean_key}") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch remote asset: {exc.reason}") from exc


def content_type_from_key(key: str) -> str:
    if key.endswith(".glb"):
        return "model/gltf-binary"
    if key.endswith((".step", ".stp")):
        return "model/step"
    guessed, _ = mimetypes.guess_type(key)
    return guessed or "application/octet-stream"
