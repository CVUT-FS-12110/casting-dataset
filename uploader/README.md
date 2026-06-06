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
metadata/brake_disc-001.json
mesh/brake_disc-001.glb
sections/brake_disc-001-x.png
sections/brake_disc-001-y.png
sections/brake_disc-001-z.png
step/brake_disc-001.step
```

Dry run:

```bash
.venv/bin/python -m uploader.upload_generated --dry-run
```

Upload. Objects are uploaded with `public-read` ACL by default. The uploader also
sets bucket CORS so the GitHub Pages browser can fetch `index.json`, metadata,
meshes, STEP files, and section images directly from S3.

```bash
.venv/bin/python -m uploader.upload_generated
```
