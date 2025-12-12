# Label Studio Local Files Restore (Docker)

This document describes the **exact, working procedure** to restore a Label Studio project
(images + annotations) from a Label Studio **JSON (tasks)** export when running Label Studio
inside Docker and serving images from the local filesystem.

This procedure was validated end-to-end.

---

## 1. Host Folder Structure (Required)

Your repository layout:

```
labeling/
  docker-compose.yml
  ls-data/
    media/
      upload/
        1/
        2/
```

All image files must live under:

```
labeling/ls-data/media/upload/<N>/*.jpg
```

---

## 2. Docker Compose Configuration

Label Studio **must** be configured to:

- Serve local files
- Use `/data` as the document root
- Expose host `ls-data/media` as container `/data`

### Minimal working service

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
      - LOCAL_FILES_SERVING_ENABLED=true
      - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/data
```

Notes:
- The `./ls-data/media:/data` mapping is critical.
- Other services (e.g., ML backends) can be ignored initially.

---

## 3. Start Label Studio

From the directory containing `docker-compose.yml`:

```bash
docker compose up -d --force-recreate labelstudio
docker compose ps
```

Verify images are visible in the container:

```bash
docker compose exec labelstudio ls /data/upload/2 | head
```

---

## 4. Create Label Studio Project

1. Open `http://localhost:8080`
2. Create a **new project**
3. (Recommended) Configure the labeling interface **before importing data**

### Example Bounding Box Interface

```xml
<View>
  <Image name="image" value="$image"/>
  <RectangleLabels name="bbox" toName="image" showInline="true">
    <Label value="class_1"/>
    <Label value="class_2"/>
  </RectangleLabels>
</View>
```

Important:
- `name` must match `from_name` in the JSON
- `toName` must match `to_name` in the JSON
- `<Label value="..."/>` strings must exactly match JSON labels

---

## 5. Configure Local Files Storage

Inside the project:

1. Settings → Cloud Storage
2. Add Source Storage → **Local files**
3. Path:
   ```
   /data/upload
   ```
4. Save

This registers the filesystem source but **does not import images** by itself.

---

## 6. Inspect the Exported JSON

Example export filename:

```
project-2-at-2025-12-11-22-46-335f7026.json
```

Run the following to inspect paths:

```bash
python3 - << 'PY'
import json
p="project-2-at-2025-12-11-22-46-335f7026.json"
d=json.load(open(p,"r"))

tasks = d if isinstance(d, list) else d.get("tasks") or []
print("Num tasks:", len(tasks))
t = tasks[0]
print("Image field:", t.get("data", {}).get("image"))
PY
```

If the image field looks like:

```
/data/upload/2/filename.jpg
```

it **must be rewritten** to a Label Studio local-files URL.

---

## 7. Rewrite JSON Image Paths (Required)

Convert filesystem-style paths to Label Studio served URLs:

```
/data/upload/2/file.jpg
→
/data/local-files/?d=upload/2/file.jpg
```

Run:

```bash
python3 - << 'PY'
import json

inp="project-2-at-2025-12-11-22-46-335f7026.json"
out="project-2-local-files.json"

d=json.load(open(inp,"r"))
for t in d:
    p=t["data"]["image"]
    if p.startswith("/data/upload/"):
        t["data"]["image"] = "/data/local-files/?d=" + p[len("/data/"):]
json.dump(d, open(out,"w"), indent=2)
print("Wrote:", out)
PY
```

This creates a **new JSON file** and leaves the original untouched.

---

## 8. Import Tasks and Annotations

In the project UI:

1. Go to **Import**
2. Select import method: **Tasks**
3. Upload:
   ```
   project-2-local-files.json
   ```

Result:
- Tasks are created
- Images render correctly
- Annotations are restored

---

## 9. Common Failure Checks

### Image exists but does not render
Verify container path:

```bash
docker compose exec labelstudio ls /data/upload/2 | head
```

Verify env vars:

```
LOCAL_FILES_SERVING_ENABLED=true
LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/data
```

### Boxes do not appear
Your labeling interface does not match the JSON:
- `from_name` ↔ control `name`
- `to_name` ↔ `<Image name=...>`
- label strings ↔ `<Label value=...>`

---

## 10. Key Concept Summary

- **Cloud Storage** only registers where files live
- **Tasks JSON** defines which images are used
- **Local files must be served via `/data/local-files/?d=...`**
- Absolute filesystem paths are not browser-loadable
- UI must match annotation schema exactly

---

This README documents the *working* configuration and should be reused for new machines.
