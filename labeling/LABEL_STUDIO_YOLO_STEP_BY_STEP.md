# Label Studio + YOLO (Local Files) — Step‑by‑Step Reproducible Setup Guide

This is a **single, linear, step‑by‑step guide**.
Follow it **top to bottom**. Do not skip steps.

Everything is centered around the **exact docker-compose.yml below**.
All verification steps are included so you do not have to “remember” anything.

---

## STEP 0 — What This Guide Assumes

- You are on a Linux host
- Docker and Docker Compose v2 are installed
- You have a copy of the `embedded_vision` repository
- You want **Label Studio + YOLO ML backend** using **local files**
- You want to avoid rediscovering API‑key, path, and model issues

If any assumption is false, stop.

---

## STEP 1 — Verify You Are in the Correct Repository

You must be at the repo root:

```bash
pwd
basename "$(pwd)"
```

Expected:
```text
embedded_vision
```

If not, `cd` until this is true.

---

## STEP 2 — Required Directory Structure (Host)

Create and verify the following directories **exactly**:

```text
embedded_vision/
├── labeling/
│   ├── docker-compose.yml
│   ├── ls-data/
│   │   └── media/
│   └── .env
├── models/
│   └── <your model files>
```

Verify:

```bash
ls labeling
ls labeling/ls-data
ls labeling/ls-data/media
ls models
```

If any directory is missing, create it now.

---

## STEP 3 — Docker Compose (AUTHORITATIVE)

Your setup is defined by this file. Do not modify unless you know why.

```yaml
services:
  labelstudio:
    image: heartexlabs/label-studio:latest
    container_name: labelstudio
    ports:
      - "8080:8080"
    volumes:
      - ./ls-data:/label-studio/data
      - ./ls-data/media:/data
    environment:
      - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/data
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LOCAL_FILES_SERVING_ENABLED=true   # backward compatibility
  yolo:
    container_name: yolo
    image: heartexlabs/label-studio-ml-backend:yolo-master
    depends_on:
      - labelstudio
    environment:
      - LABEL_STUDIO_HOST=http://labelstudio:8080
      - LABEL_STUDIO_API_KEY=${LABEL_STUDIO_API_KEY}
      - LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN=true
    ports:
      - "9090:9090"
    volumes:
      - ../models:/app/models
```

Key consequences (facts):
- Images must be under `labeling/ls-data/media/`
- Inside Label Studio, images appear at `/data`
- Models must be under `embedded_vision/models/`
- Inside YOLO container, models appear at `/app/models`

---

## STEP 4 — API Tokens (CRITICAL)

Label Studio has **two token types**:

1. **Personal Access Token (PAT)**  
   - Default in UI
   - **WILL FAIL**
   - Produces `401 Unauthorized` errors

2. **Legacy API Token**  
   - **REQUIRED**
   - Must be enabled in UI and backend

### 4.1 Enable Legacy Tokens in UI

In Label Studio UI:
- Enable **Legacy API Tokens**: Go to Organization -> API Token Settings -> Legacy Tokens
- Generate a **legacy token**: Account and Settings -> Legacy Token -> Copy

### 4.2 Store Token in `.env`

`labeling/.env`:

```env
LABEL_STUDIO_API_KEY=<legacy_token_here>
```

A PAT WILL NOT WORK.

---

## STEP 5 — Start the System

From `labeling/`:

```bash
docker compose up -d
```

Verify containers:

```bash
docker compose ps
```

Expected:
- `labelstudio` → running
- `yolo` → running

If not, inspect logs now.

---

## STEP 6 — Verify API Key Is Loaded (Do Not Skip)

```bash
docker compose exec yolo env | grep LABEL_STUDIO_API_KEY
```

Expected:
- token printed

If empty:
- `.env` is wrong
- OR containers were not restarted

Fix before continuing.

---

## STEP 7 — Verify Direct File Access via API (MOST IMPORTANT CHECK)

This checks whether auth + local files actually work.

```bash
docker compose exec yolo sh -lc '
python - <<PY
import os, requests
tok = os.environ["LABEL_STUDIO_API_KEY"]
url = "http://labelstudio:8080/api/projects"
r = requests.get(url, headers={"Authorization": f"Token {tok}"})
print("status:", r.status_code)
PY
'
```

Results:
- `200` → API key is valid
- `401` → WRONG TOKEN TYPE (PAT)
- anything else → stop and debug

Do NOT proceed until this returns 200.

---

## STEP 8 — Verify Model Visibility

```bash
docker compose exec yolo ls /app/models
```

Expected:
- at least one model file

If empty:
- predictions will fail

Label Studio does NOT upload models.

---

## Section 9 — Data Handling in Label Studio (Important Clarification)

### 9.1 Local Files: How Data Is Actually Added

For this workflow, you typically do not need to configure Local Storage in the UI for JSON imports when using the /data/local-files/?d=... pattern.
Local file access is enabled by Docker volume mounts **and** the `LABEL_STUDIO_LOCAL_FILES_*` environment variables in `docker-compose.yml`:

```yaml
volumes:
  - ./ls-data:/label-studio/data
  - ./ls-data/media:/data
environment:
  - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/data
  - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
```

As a result:

- Any files placed on the host under:
  ```text
  labeling/ls-data/media/
  ```
  are visible inside the container under `/data/...`.
- JSON tasks will refer to those files using the **local-files URL**:
  ```text
  /data/local-files/?d=<relative-path-under-/data>
  ```
- Files can be uploaded directly through the UI **or**
  simply copied into the directory on disk.

**Filesystem presence plus the `/data/local-files/?d=...` URL is the source of truth.**

Verification:
```bash
docker compose exec labelstudio ls /data
```

If files appear here, Label Studio can serve them via `/data/local-files/?d=...`.

---

### 9.2 Importing Images

There are two supported paths:

#### A) Direct filesystem import (preferred)

1. Copy images to:
   ```text
   labeling/ls-data/media/upload/<data_dir>/<file>.jpg
   ```
2. When constructing or rewriting JSON tasks, point each image to:
   ```text
   /data/local-files/?d=upload/<data_dir>/<file>.jpg
   ```
3. Open the project in Label Studio and import the JSON.

No GUI storage configuration is required for this local-files URL pattern.

#### B) Upload via UI

- Uploading images via the UI places them under:
  ```text
  /label-studio/data/upload
  ```
- This also works, but mixes managed uploads with local files and is not what this guide optimizes for.

Both methods work; this guide assumes **direct filesystem + `/data/local-files/?d=...` URLs**.

---

## Section 10 — Importing Annotation JSON (Local-Files URL)

### 10.1 JSON Imports Use the `/data/local-files/?d=...` Pattern

When importing **annotation JSON**, this guide uses the **local-files handler**, not Cloud Storage.

Given:

```yaml
LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/data
```

and images under:

```text
/data/upload/...
```

your JSON `image` values must be of the form:

```json
"image": "/data/local-files/?d=upload/<subdirs>/<file>.jpg"
```

Examples:

```json
"image": "/data/local-files/?d=upload/2/example.jpg"
"image": "/data/local-files/?d=upload/toy_cars/example_001.jpg"
```

This pattern is portable across machines and does **not** depend on Label Studio’s upload database.

---

### 10.2 Required JSON Path Adjustment

Annotation JSON files often contain references like:

```json
"image": "/data/media/example.jpg"
```

or:

```json
"image": "/data/upload/example.jpg"
```

These will **not** work reliably in newer Label Studio versions.

They must be rewritten to the **local-files** form:

```json
"image": "/data/local-files/?d=upload/example.jpg"
```

or, more generally:

```json
"image": "/data/local-files/?d=<relative-path-under-/data>"
```

where `<relative-path-under-/data>` matches the on-disk layout inside `/data`.

---

### 10.3 Example Python Script to Rewrite JSON Paths

Use this before importing JSON:

```python
import json
from pathlib import Path

in_file = Path("input_annotations.json")
out_file = Path("fixed_annotations.json")

with in_file.open() as f:
    data = json.load(f)

for task in data:
    if "data" in task and "image" in task["data"]:
        p = task["data"]["image"]

        # Normalize any of these:
        #   "/data/media/upload/2/..."
        #   "/data/upload/2/..."
        #   "upload/2/..."
        #   "/upload/2/..."
        # down to: "upload/2/..."
        if p.startswith("/data/"):
            p = p[len("/data/"):]           # "media/upload/2/..." or "upload/2/..."
        if p.startswith("media/"):
            p = p[len("media/"):]           # "upload/2/..."
        if p.startswith("/"):
            p = p[1:]                       # "upload/2/..."

        # Final, LS-approved form:
        task["data"]["image"] = f"/data/local-files/?d={p}"

with out_file.open() as f:
    json.dump(data, f, indent=2)

print("Wrote:", out_file)
```

Then import `fixed_annotations.json` via the Label Studio UI.

---

### 10.4 Summary of Data Paths (Authoritative)

| Purpose                | Path / Pattern                                      |
|------------------------|-----------------------------------------------------|
| Local filesystem root  | `/data`                                             |
| On-disk images         | `/data/upload/...`                                  |
| JSON annotation import | `/data/local-files/?d=upload/<subdirs>/<file>.jpg` |

---

### Final Rule

> **Local files are enabled by container mounts + `LABEL_STUDIO_LOCAL_FILES_*` env vars.**  
> **JSON imports must use `/data/local-files/?d=<relative-path-under-/data>`, not `/data/upload/...`.**

---

### 10.5 TBD

---

### 10.6 Wiring the YOLO Model into the Labeling Interface (Required)

This section documents the **Label Studio UI configuration** required to
enable YOLO model predictions.

It assumes:
- Containers are already running via docker-compose
- The YOLO backend is reachable
- Models are mounted at `/app/models` inside the YOLO container

---

#### 10.6.1 Open the Labeling Configuration Editor

In the Label Studio UI:

1. Open your project
2. Go to **Settings**
3. Select **Labeling Interface**
4. Switch to **Code View**

This XML defines how data, labels, and models are connected.

---

#### 10.6.2 Add `model_path` to the Labeling XML

Below is a **working example** of a labeling configuration that enables YOLO predictions.

```xml
<View>
  <View style="display:flex;align-items:start;gap:8px;flex-direction:column-reverse">
    <Image name="image" value="$image" zoom="true" zoomControl="false"/>
    <RectangleLabels
      name="bb"
      toName="image"
      showInline="true"
      model_path="/app/models/toy_cars.pt"
      model_score_threshold="0.5"
    >
      <Label value="yellow" background="#FFA39E"/>
      <Label value="black" background="#D4380D"/>
      <Label value="orange" background="#FFC069"/>
      <Label value="cyan" background="#AD8B00"/>
      <Label value="blue" background="#D3F261"/>
      <Label value="grey" background="#389E0D"/>
      <Label value="pink" background="#5CDBD3"/>
      <Label value="red" background="#096DD9"/>
      <Label value="white" background="#ADC6FF"/>
      <Label value="vet" background="#FFA39E"/>
    </RectangleLabels>
  </View>

  <!-- Axis-aligned bounding boxes only -->
</View>
```

**Key points:**

- `model_path="/app/models/toy_cars.pt"`
  - Path is resolved **inside the YOLO container**
  - `/app/models` exists because of docker-compose
  - The file **must exist**, or predictions silently fail

- `model_score_threshold="0.5"`
  - Optional
  - Controls confidence cutoff for predictions

Label Studio does **not** validate `model_path`.

---

#### 10.6.3 Register the YOLO Backend in the UI

If not already done:

1. Go to **Settings**
2. Select **Machine Learning**
3. Click **Add Model**
4. Enter the backend URL:

```text
http://yolo:9090
```

5. Save

No model file is uploaded or selected here.
This step only tells Label Studio **where the backend lives**.

---

#### 10.6.4 Save and Reload

After updating the labeling XML:

1. Click **Save**
2. Reload the project page

Predictions should now appear automatically when opening tasks.

---

#### 10.6.5 Common Failure Modes

- Backend registered but no predictions:
  - `model_path` missing or incorrect
- Wrong path produces **no UI error**
- Model selection is **not** done in the UI

---

#### 10.6.6 Monitor YOLO Predictions

You can issue the following command to monitor the YOLO predictions.

```bash
docker compose logs -f yolo
```

In the Label Studio front end, when you select an image, you should see something like the following.

```bash
yolo  | image 1/1 /root/.cache/label-studio/0f6197fb__7d1c606c-ff5db76f-20251210_093346_379821.jpg: 384x640 1 orange, 67.8ms
yolo  | Speed: 1.2ms preprocess, 67.8ms inference, 0.3ms postprocess per image at shape (1, 3, 384, 640)
```

**Rule:**  
> YOLO predictions require BOTH backend registration and a valid `model_path` in the labeling XML.


## STEP 11 — YOLO Backend Registration

In Label Studio:
- Settings → ML Backend
- URL: `http://yolo:9090`
- Save

Verify backend logs:

```bash
docker compose logs yolo
```

No errors expected.

---

## STEP 12 — Annotation Rules (MANDATORY)

Before exporting to YOLO:

- DELETE all existing annotations
- Ensure EXACTLY ONE annotation per task

If you do not do this:
> Exported YOLO labels are untrustworthy.

---

## STEP 13 — Bounding Box Format (Fact)

Label Studio:
- `(x_min, y_min, x_max, y_max)`

YOLO:
- `(x_center, y_center, width, height)`
- normalized `[0,1]`

Conversion assumes single annotation.

---

## STEP 14 — Tear Down / Rebuild

Preserve data:

```bash
docker compose down
docker compose up -d
```

Full reset (destructive):

```bash
docker compose down -v
```

---

## STEP 15 — Debug Order (If Anything Fails)

Always check in this order:

1. Legacy token enabled in UI
2. `LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN=true` present
3. Token visible inside YOLO container
4. Direct API file fetch returns 200
5. Model visible in `/app/models`
6. Only then check UI behavior

---

## FINAL RULE

> If you see `401`, you are using the wrong token **or the wrong image URL pattern**.  
> Fix the token and ensure JSON uses the correct image URL mode for this machine
(/data/local-files/?d=... recommended, /data/upload/... legacy — see Appendix A).

# Appendix A — Backward Compatibility Notes (Two Image-Path Modes)

This appendix documents the **two image-path modes** we’ve observed across machines, why they differ, and **exactly what changes** (if any) you must make to keep things working without relearning this again.

---

## A.1 The Two Modes

### Mode A (Recommended / Portable): `local-files` URL
**Use when:** you want the most reproducible behavior across fresh installs / newer Label Studio builds.

**JSON `image` field pattern (authoritative):**
```text
/data/local-files/?d=<relative-path-under-LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT>
```
Example (your proven-good case):
```text
/data/local-files/?d=upload/2/bb2ef195-20251210_084508_714810.jpg
```

**Why this works:** it uses Label Studio’s local-file proxy handler, which is designed for serving mounted files. Current docs explicitly describe this prefix. 

---

### Mode B (Legacy / “Worked on the other machine”): direct `/data/upload/...`
**Use when:** your other machine/project already works with direct paths like:
```text
/data/upload/<...>
```
and you don’t want to disturb that workflow.

**JSON `image` field pattern (legacy):**
```text
/data/upload/<subdirs>/<file>
```
Example:
```text
/data/upload/2/bb2ef195-20251210_084508_714810.jpg
```

**Important warning:** In newer Label Studio builds this often fails with auth/URL-loading issues (401 / “issue loading URL”), which is why Mode A exists and is documented. 

---

## A.2 Docker Compose: “Keep Both Flags” for Maximum Compatibility

Different Label Studio builds/docs have historically referenced different enable flags (this inconsistency is real and has been reported).

To avoid surprises, **keep both** in `labelstudio.environment`:

```yaml
environment:
  - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/data
  - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
  - LOCAL_FILES_SERVING_ENABLED=true   # legacy compatibility (some older docs/images mention it)
```

Notes:
- Modern docs commonly reference the `LABEL_STUDIO_LOCAL_FILES_*` variables. 
- Older versions/issues/messages sometimes reference `LOCAL_FILES_SERVING_ENABLED`. 

---

## A.3 Directory Layout (Host ↔ Container)

Given your compose mounts:

```yaml
volumes:
  - ./ls-data:/label-studio/data
  - ./ls-data/media:/data
```

Then:

### Host
```text
embedded_vision/labeling/ls-data/media/upload/...
```

### Label Studio container
```text
/data/upload/...
```

This is true for **both** Mode A and Mode B.

---

## A.4 “Which mode am I in?” (10-second test)

Pick a known file and test in your browser:

### Test 1 — local-files (Mode A)
```text
http://localhost:8080/data/local-files/?d=upload/2/<file>.jpg
```
- If it loads: Mode A is available (recommended).

### Test 2 — direct upload path (Mode B)
```text
http://localhost:8080/data/upload/2/<file>.jpg
```
- If this loads *without* 401/URL errors: Mode B is supported in that environment.
- If it returns 401/URL errors: use Mode A.

---

## A.5 JSON Rewrite Scripts (Both Modes)

### A.5.1 Rewrite to Mode A (`/data/local-files/?d=...`)  ✅ recommended
```python
import json
from pathlib import Path

in_file = Path("input.json")
out_file = Path("fixed_mode_a.json")

with in_file.open() as f:
    data = json.load(f)

for task in data:
    if "data" in task and "image" in task["data"]:
        p = task["data"]["image"]

        # Normalize to: "upload/..."
        if p.startswith("/data/"):
            p = p[len("/data/"):]            # "media/upload/..." or "upload/..."
        if p.startswith("media/"):
            p = p[len("media/"):]            # "upload/..."
        if p.startswith("/"):
            p = p[1:]                        # "upload/..."

        task["data"]["image"] = f"/data/local-files/?d={p}"

with out_file.open("w") as f:
    json.dump(data, f, indent=2)

print("Wrote:", out_file)
```

### A.5.2 Rewrite to Mode B (`/data/upload/...`)  ⚠ legacy
Use this only if your environment/browser test shows `/data/upload/...` loads successfully.

```python
import json
from pathlib import Path

in_file = Path("input.json")
out_file = Path("fixed_mode_b.json")

with in_file.open() as f:
    data = json.load(f)

for task in data:
    if "data" in task and "image" in task["data"]:
        p = task["data"]["image"]

        # Normalize to: "upload/..."
        if p.startswith("/data/"):
            p = p[len("/data/"):]            # "media/upload/..." or "upload/..."
        if p.startswith("media/"):
            p = p[len("media/"):]            # "upload/..."
        if p.startswith("/"):
            p = p[1:]                        # "upload/..."

        task["data"]["image"] = f"/data/{p}" # => "/data/upload/..."

with out_file.open("w") as f:
    json.dump(data, f, indent=2)

print("Wrote:", out_file)
```

---

## A.6 Practical Guidance (So you don’t get bitten again)

- Put **Mode A** in the “mainline” workflow when you want portability and fewer surprises. Current docs explicitly call out the `/data/local-files/?d=` prefix. 
- Keep **Mode B** available as a legacy option, but gate it behind the simple browser test in A.4.
- Keep **both enable flags** in compose for cross-machine compatibility (A.2).

