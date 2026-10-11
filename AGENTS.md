# AGENTS.md

Population information management system: Python/Flask server, PyQt6 desktop client, Flutter mobile app, vanilla JS web frontend.

## Quick Commands

```bash
# Server (production)
./start_server.sh start 5000 production   # gunicorn + SSL
./start_server.sh start 5000 development  # Flask debug mode
./start_server.sh stop / status / backup

# Server (manual)
cd server && source venv/bin/activate && python app_modular.py

# Desktop
./start_desktop.sh start local                            # direct SQLite
./start_desktop.sh start network https://server:5000      # HTTP client mode

# Mobile (Flutter)
cd mobile && flutter pub get && flutter build apk --release
flutter test                          # run all tests
flutter test test/utils/validators_test.dart  # single test file
./build_mobile.sh all https://server:5000   # config + deps + test + analyze + build

# Server validation (syntax + imports only, NOT unit tests)
cd server && python test_modules.py

# Install / upgrade / uninstall
./install.sh              # full setup (creates venvs, data dirs, SSL certs, systemd service)
./install.sh verify       # check installation
./install.sh upgrade      # backup DB + upgrade deps + restart
./install.sh reinstall    # isolated venvs (no --system-site-packages)
./install.sh uninstall    # interactive; --keep-data preserves data/
```

## Architecture

### Four frontends, one server

| Component | Location | Entry point | Tech |
|-----------|----------|-------------|------|
| Server | `server/` | `app_modular.py` (use this) | Flask + SQLAlchemy + SQLite |
| Legacy server | `backup_legacy/` | `web_app.py` (~4400 lines, 已归档) | Monolithic, avoid for new work |
| Web frontend | `server/web_static/` | `index.html` + `app.js` (~2086 lines) + `style.css` | Vanilla JS, no framework, no build step |
| Desktop | `desktop/` | `main.py` (~2250 lines) | PyQt6, monolithic |
| Mobile | `mobile/` | `lib/main.dart` | Flutter, Dart >=3.5.0 |

### Server API modules (Flask blueprints)

17 blueprints in `server/api/`, exported in `server/api/__init__.py`, registered in `app_modular.py` via `register_blueprint()`. To add a module:
1. Create `server/api/new_module.py` with `bp = Blueprint(...)`
2. Export in `server/api/__init__.py`
3. Register in `app_modular.py` with `url_prefix='/api'`

Modules: `auth`, `users`, `persons` (people + families), `students` (education), `photos`, `statistics`, `import_export` (Excel), `backup`, `logs` (audit), `notifications`, `reports`, `report_files`, `land_subsidy`, `treatment_payment`, `pension_insurance`, `dibao_payment`, `tekun_payment`, `update` (checks GitHub releases for app updates).

**CORS is hardcoded to `*`** in `app_modular.py` (`CORS(app, resources={r"/api/*": {"origins": "*"}})`). The `allowed_origins` list in `config.yaml` is **not enforced** — editing it has no effect.

### Desktop dual mode

- **Local mode**: direct SQLite access via `desktop/core/database.py`
- **Network mode**: HTTP client via `desktop/network/client.py`, talks to server API

Both modes share the same UI code in `desktop/main.py`. Mode is set via env vars `POPULATION_MODE` / `POPULATION_SERVER_URL` (see `start_desktop.sh`).

### Mobile offline-first

Mobile caches data locally and syncs when online. Key services:
- `services/offline_data_service.dart` — offline queue
- `services/sync_service.dart` — sync logic with retry
- `services/connectivity_service.dart` — network detection

### Web frontend (server/web_static/)

This is the "desktop browser" UI served by Flask. Single-page app in vanilla JS (`app.js`, ~2086 lines). When the user says "desktop端" or "桌面端" in the context of web features, they mean this — NOT the PyQt6 desktop app.

## Key Data Patterns

### Grade system

Database stores grade **codes** (`G1`, `K2`, etc.), defined in `server/config.py`:
- `GRADES` — ordered list of codes
- `GRADE_DISPLAY` — code → Chinese label (`"G1": "小学1年级"`)
- `GRADE_CODE_MAP` — reverse: Chinese → code (for saving from mobile/web)
- `GRADE_PROMOTION_MAP` — next grade for batch promotion

Mobile and web send Chinese names ("一年级"). Server converts via `GRADE_CODE_MAP` on save, `GRADE_DISPLAY` on read. Desktop uses codes directly.

### Land area change tracking

When `land_area` changes, the system requires a `land_area_change_reason`. Both mobile and web prompt for this before saving. Server stores the reason and timestamp.

### Authentication

JWT tokens via `server/utils/security.py`. Tokens expire after `TOKEN_EXPIRY_HOURS` (default 2). Password hashing uses argon2 (preferred) with SHA256 fallback. Login lockout after `LOGIN_LOCK_ATTEMPTS` (5) failures for `LOGIN_LOCK_MINUTES` (15).

Default admin: `admin` / `admin123` — created on first run via `_ensure_default_admin()` in `api/auth.py`, should be replaced immediately.

## Configuration

### Server config: `server/config.yaml`

`config.yaml` is **gitignored** (contains secrets via `${VAR_NAME}` env substitution). Template is `config.example.yaml` at repo root — `start_server.sh` and `install.sh` copy it to `server/config.yaml` on first run. Key sections:
- `domains.primary` / `domains.intranet` — dual-domain support (IPv6 + LAN)
- `database.type` — `sqlite` (default) or `postgresql`
- `security.ssl` — cert paths and self-signed cert settings

### Data directory: `data/`

Created at runtime (gitignored). Contents: `population.db`, `Photos/`, `backups/`, `logs/`, `certs/`, `reports/`.

**Data dir can be relocated.** `server/config.py` `get_data_dir()` reads an encrypted path from `~/.config/人口通/data_path.conf` (or `%APPDATA%` on Windows). If that file exists, the DB and all data subdirs live there instead of `server/`. Check this first if the database seems missing.

**`ensure_dirs()` must be called at startup.** `app_modular.py` calls `config.ensure_dirs()` before `init_db()`. If you add a new data subdir to `config.py`, add it to `ensure_dirs()` too — otherwise the directory won't exist and operations will fail with 500 errors (this caused report upload failures before).

### SSL

Server is **always HTTPS**. In production, gunicorn starts with `--certfile` / `--keyfile` from `data/certs/`. In dev (`app_modular.py`), `ssl_utils.generate_self_signed_cert()` (at `server/ssl_utils.py`, not `server/utils/`) auto-generates a self-signed cert if none exists. Clients use certificate pinning — `cert_manager.py` at repo root manages generate/backup/export/deploy of certs to desktop and mobile.

### Mobile API URL: `mobile/lib/config/app_config.dart`

Set at build time via `./build_mobile.sh config https://server:5000`, or changed at runtime in app settings.

**`AppConfig.getApiUrl()` is dead code.** It prepends `/api/v1` but the server has no `/api/v1` prefix — blueprints register at `/api/`. All actual API calls in `mobile/lib/api/` and `mobile/lib/services/` use `/api/...` paths directly on the Dio client (whose `baseUrl` is `AppConfig.apiBaseUrl`). Do not use `getApiUrl()` for new API calls.

### Mobile certificate pinning is bypassed

`api_client.dart` loads a cert from `assets/certs/server.crt` for pinning, but `badCertificateCallback` unconditionally returns `true` (line 235), so invalid/self-signed certs are always accepted regardless. Effective security depends on network-level trust, not app-level pinning.

## systemd Service and Detached Subprocess Pattern

### `deploy/population-server.service` is a stale template

`install.sh` generates the real service file with its **own inline heredoc** (lines 624-655), NOT by copying `deploy/population-server.service`. The install.sh version includes `KillMode=process` and `TZ=Asia/Shanghai` which the template file does NOT have. **Editing `deploy/population-server.service` has no effect** — edit the heredoc in `install.sh` instead.

### `KillMode=process` is critical

The deployed service file must have `KillMode=process`. Without it, systemd's default `KillMode=control-group` kills all processes in the cgroup when stopping the service, including detached subprocesses. Two features depend on this:

1. **Server code update** (`server/api/update.py`): forks a detached bash subprocess that does `git pull` → `systemctl restart population-server`. The subprocess must survive the restart.
2. **Backup restore** (`server/api/backup.py` and `web_app.py`): forks a detached bash subprocess that does `systemctl stop` → `cp DB` → `systemctl start`. The subprocess must survive the stop.

Both use `subprocess.Popen(['bash', '-c', script], start_new_session=True)` — `start_new_session=True` creates a new session, and `KillMode=process` ensures systemd only kills the main gunicorn process, not the detached child.

### Never overwrite a live SQLite DB

`restore_database()` in `server/excel_importer.py` does `shutil.copy2(backup_db, DB_PATH)` while gunicorn has open connections — this corrupts the database (`database disk image is malformed`). Both `api/backup.py` and `web_app.py` now avoid calling `restore_database()` directly and instead use the detached subprocess pattern (stop server first, then copy). Do not call `restore_database()` from any server endpoint.

### Remote deploy

```bash
sshpass -p '1234' ssh root@192.168.9.26 "cd /root/population-system && git pull origin master && find server -name '*.pyc' -delete && find server -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; systemctl restart population-server"
```

Remote code path: `/root/population-system`. DB at `server/population.db` (no `data_path.conf` on remote, so `DATA_DIR` resolves to `server/`). systemd service: `population-server`.

## Testing

```bash
cd server && python test_modules.py   # syntax + import checks only
cd mobile && flutter test             # real unit + widget tests
```

**Server has no unit tests.** `test_modules.py` only verifies Python syntax and imports — and it doesn't cover all modules. It checks syntax for 14 files and imports only 11 of 17 blueprints; `land_subsidy`, `treatment_payment`, `pension_insurance`, `dibao_payment`, `tekun_payment`, and `update` are not checked at all. Mobile has unit tests for validators, models, network cache, and pagination (8 test files in `mobile/test/`).

**Always run `python3 -c "import py_compile; py_compile.compile('<file>', doraise=True)"` after editing server Python files** — this catches syntax errors that `test_modules.py` would also catch, but faster for a single file.

## Docker

```bash
cd server && docker build -t population-server .
docker run -p 5000:5000 -v /path/to/data:/app/data population-server
```

**Gotcha**: Dockerfile CMD uses `web_app:app` (legacy). For modular version, override: `CMD ["gunicorn", "--config", "gunicorn_config.py", "app_modular:app"]`

## Virtual Environments

- `server/venv/` — Flask, SQLAlchemy, pandas, Pillow, cryptography, argon2
- `desktop/venv/` — PyQt6

Default install uses `--system-site-packages` (reuses system-installed packages). Use `./install.sh reinstall` for isolated venvs.

## Photo Types

Expected types: `身份证`, `社保卡1`, `社保卡2`, `社保卡3`. Extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`. Defined in `server/config.py` (`PHOTO_TYPES`, `PHOTO_EXTENSIONS`).

## Backup Structure

Backups live in `data/backups/` as directories named `backup_YYYYMMDD_HHMMSS/`. Each contains `population.db`, optionally `photos.tar.gz`, and a `backup_complete.txt` manifest (JSON with `timestamp`, `encrypted`, `manual`, `db_hash`). `get_backup_list()` only lists directories starting with `backup_` that contain `backup_complete.txt` — bare `.db` files in `backups/` are invisible to the API and cannot be deleted or restored through any client.

## Desktop Build

Desktop is packaged with PyInstaller (onedir mode) into a ZIP distributed via GitHub Release. After server or desktop code changes, the desktop package must be rebuilt and re-uploaded. **Do NOT auto-build APK** — only remind the user to rebuild manually via `./build_mobile.sh all https://server:5000`.
