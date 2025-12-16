# Docker Compose User Guide (Label Studio + YOLO)

This standalone guide explains **how to use Docker Compose** for the Label Studio + YOLO setup.  
It is written for users who know Docker but **have never used docker-compose**.

All commands assume you are inside:

```
embedded_vision/labeling/
```

Your `docker-compose.yml` must be located here.

---

# 1. Start Everything

Start Label Studio **and** YOLO backend:

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

---

# 2. Stop Everything

```bash
docker compose down
```

Data on disk is preserved.

---

# 3. Restart Everything (Most Common)

```bash
docker compose down
docker compose up -d
```

Use this after:
- Editing `.env`
- Adding models
- Changing directory structure

---

# 4. Hard Reset (Deletes Volumes — Destructive)

Use only when installation is corrupted:

```bash
docker compose down -v
```

This deletes:
- Label Studio DB  
- Uploads  
- Cached backend data  

---

# 5. Logs

Both services:

```bash
docker compose logs -f
```

YOLO only:

```bash
docker compose logs -f yolo
```

Label Studio only:

```bash
docker compose logs -f labelstudio
```

---

# 6. Exec Into a Container

Label Studio shell:

```bash
docker compose exec labelstudio bash
```

YOLO backend shell:

```bash
docker compose exec yolo bash
```

Useful for:
- Checking `/app/models`
- Verifying token loading
- Debugging path issues

---

# 7. Rebuild (Rarely Needed)

Your setup **pulls images**, but if you later add a Dockerfile:

```bash
docker compose build
```

---

# 8. Run Only One Service

Start only Label Studio:

```bash
docker compose up -d labelstudio
```

Start only YOLO backend:

```bash
docker compose up -d yolo
```

---

# 9. Environment Variable Verification

Check if the YOLO container received your API key:

```bash
docker compose exec yolo env | grep LABEL_STUDIO_API_KEY
```

If blank → `.env` not loaded → restart containers.

---

# 10. Check Mounted Paths

Label Studio should see media here:

```bash
docker compose exec labelstudio ls /data
```

YOLO should see model files here:

```bash
docker compose exec yolo ls /app/models
```

---

# 11. Quick Reference Table

| Task | Command |
|------|---------|
| Start everything | `docker compose up -d` |
| Stop everything | `docker compose down` |
| Restart | `docker compose down && docker compose up -d` |
| Hard reset | `docker compose down -v` |
| Check status | `docker compose ps` |
| Logs (YOLO) | `docker compose logs -f yolo` |
| Logs (LS) | `docker compose logs -f labelstudio` |
| Exec into container | `docker compose exec <service> bash` |
| List service files | `docker compose exec <service> ls /path` |

---

# 12. Core Rule

Everything is run from the `labeling/` directory, and `docker compose` manages BOTH Label Studio and YOLO as one system.

