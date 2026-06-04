# Casting dataset

Parametric CAD generators for synthetic cast-iron casting datasets.

> http://147.32.173.190:9011/

## Generate Assets

The generator creates the representative brake disc models described in
`docs/categories/breake_dics.md`. Outputs use catalog IDs such as `001-001`.

CadQuery currently supports Python 3.10-3.12 best. From a compatible environment:

```bash
python -m pip install -r requirements.txt
```

Generate all STEP files, GLB meshes, section images, metadata, and `generated/index.json`:

```bash
.venv/bin/python src/categories/generate.py
```

Brake-disc-only wrapper:

```bash
.venv/bin/python src/categories/generate_brake_disc_assets.py
```

Generate only STEP files plus metadata/index:

```bash
.venv/bin/python src/categories/generate.py --only-steps
```

Generate only category `001`:

```bash
.venv/bin/python src/categories/generate.py --only-category 001
```

Generate only one model:

```bash
.venv/bin/python src/categories/generate.py --only-model 001-003
```

Generate only STEP for one model:

```bash
.venv/bin/python src/categories/generate.py --only-steps --only-model 001-003
```

Skip index rebuilding during generation:

```bash
.venv/bin/python src/categories/generate.py --only-model 001-003 --no-index
```

Rebuild `generated/index.json` from all metadata files:

```bash
.venv/bin/python src/categories/reindex.py
```

This also writes `generated/index.csv` for spreadsheet import.

## Upload Assets

The uploader ships the flat browser asset layout to an S3-compatible bucket:

```text
index.json
index.csv
metadata/001-001.json
mesh/001-001.glb
sections/001-001-x.png
step/001-001.step
```

It reads bucket credentials from `.env`. Required keys:

```text
ACCESS_KEY = ...
SECRET_KEY = ...
ENDPOINT = ...
BUCKET = ...
```

Preview the upload plan without sending files:

```bash
.venv/bin/python -m uploader.upload_generated --dry-run
```

Upload the generated assets. Objects are uploaded with `public-read` ACL by default:

```bash
.venv/bin/python -m uploader.upload_generated
```

For the current CESNET-style tenant bucket, the remote browser bucket URL has this
shape:

```text
https://s3.cl4.du.cesnet.cz/<GROUP>:<BUCKET>
```

Run the browser against uploaded S3 files through the local same-origin proxy:

```bash
.venv/bin/python browser/run.py --host 0.0.0.0 --port 9011 --bucket-url https://s3.cl4.du.cesnet.cz/<GROUP>:<BUCKET>
```

See `uploader/README.md` and `browser/README.md` for more details.
