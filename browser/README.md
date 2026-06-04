# Generated Model Browser

Static browser pages for generated model assets.

```bash
python -m pip install fastapi uvicorn
python -m browser.run
```

Open http://127.0.0.1:9010.

The FastAPI test server serves:

```text
/          docs/index.html landing page
/browser/  generated model browser
```

## Modes

Local mode is the default. FastAPI serves the static pages and fakes a flat bucket at
`/generated` from the local nested folders.

Real bucket mode points the static pages at a same-origin FastAPI proxy. The
server fetches the remote bucket files, so the browser is not blocked by missing
S3 CORS headers:

```bash
python -m browser.run --bucket-url https://example-bucket.example.com
```

You can also pass `?bucket=https://example-bucket.example.com` in the page URL to
fetch the bucket directly from the browser. That direct static mode requires CORS
on the bucket.

## Flat Bucket Layout

The browser expects these keys:

```text
index.json
metadata/001-001.json
mesh/001-001.glb
sections/001-001-x.png
sections/001-001-y.png
sections/001-001-z.png
step/001-001.step
```

Locally those are mapped back to:

```text
generated/metadata/brake_discs/001-001.json
generated/mesh/brake_discs/001-001.glb
generated/sections/brake_discs/001-001-x.png
generated/step/brake_discs/001-001.step
```

## Run broswer

Local:
> .venv/bin/python browser/run.py --host 0.0.0.0 --port 9011

Remote: 
> .venv/bin/python browser/run.py --host 0.0.0.0 --port 9011 --bucket-url https://s3.cl4.du.cesnet.cz/32e8087b_6cd9_4cd6_95a4_8fce18348178:casting-dataset-static
