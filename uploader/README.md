# Generated Asset Uploader

Uploads the static browser assets to an S3-compatible bucket using credentials from
`.env`.

Required `.env` keys:

```text
ACCESS_KEY = ...
SECRET_KEY = ...
ENDPOINT = ...
BUCKET = ...
```

The upload uses the flat bucket layout expected by the browser:

```text
index.json
index.csv
metadata/001-001.json
mesh/001-001.glb
sections/001-001-x.png
sections/001-001-y.png
sections/001-001-z.png
step/001-001.step
```

Dry run:

```bash
.venv/bin/python -m uploader.upload_generated --dry-run
```

Upload. Objects are uploaded with `public-read` ACL by default:

```bash
.venv/bin/python -m uploader.upload_generated
```
