# Casting dataset

Parametric CAD generators for synthetic cast-iron casting datasets.

> http://147.32.173.190:9011/

## Generate Assets

The generator creates the representative brake disc models described in
`docs/categories/brake_disc.md`. Outputs use catalog IDs such as `brake_disc-001`.

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
.venv/bin/python src/categories/brake_disc/generate_brake_disc_assets.py
```

Generate only STEP files plus metadata/index:

```bash
.venv/bin/python src/categories/generate.py --only-steps
```

Generate only category `brake_disc`:

```bash
.venv/bin/python src/categories/generate.py --only-category brake_disc
```

Generate only one model:

```bash
.venv/bin/python src/categories/generate.py --only-model brake_disc-003
```

Generate only STEP for one model:

```bash
.venv/bin/python src/categories/generate.py --only-steps --only-model brake_disc-003
```

Skip index rebuilding during generation:

```bash
.venv/bin/python src/categories/generate.py --only-model brake_disc-003 --no-index
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
metadata/brake_disc-001.json
mesh/brake_disc-001.glb
sections/brake_disc-001-x.png
step/brake_disc-001.step
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

Upload the generated assets. Objects are uploaded with `public-read` ACL by default,
and the uploader configures bucket CORS for the static browser:

```bash
.venv/bin/python -m uploader.upload_generated
```

For the current CESNET-style tenant bucket, the remote browser bucket URL has this
shape:

```text
https://s3.cl4.du.cesnet.cz/<TENANT>:<BUCKET>
```

Run the browser against uploaded S3 files through the local same-origin proxy:

```bash
.venv/bin/python browser/run.py --host 0.0.0.0 --port 9011 --bucket-url https://s3.cl4.du.cesnet.cz/<TENANT>:<BUCKET>
```

See `uploader/README.md` and `browser/README.md` for more details.
