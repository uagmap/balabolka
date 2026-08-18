# Balabolka Bot

Telegram bot for generating Russian TTS announcements and mounting them to a network share as `alarm.wav`. Built around Silero TTS and SMB access to a shared folder that downstream PA/notification systems pick up.

## What It Does

- Generates Russian speech from Cyrillic text (Silero v5.5, five voices).
- Previews all voices via `/tts` without touching the network folder.
- Mounts or removes `alarm.wav` on an SMB share via `/alarm`.
- Lists files in the alarm directory with `/files`.
- Restricts `/alarm` to a whitelist; admin manages access from Telegram.
- Runs in Docker with optional Xray sidecar for Telegram API egress and a watchdog that restarts stuck containers.

## Requirements

- Docker Engine and Docker Compose (recommended), or Python 3.11+ for local runs
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Reachable SMB share for alarm files (`//server/share/path` style)
- Outbound HTTPS to `models.silero.ai` on first TTS use (model download)
- If Telegram is blocked from your network: a working VLESS REALITY tunnel and filled `xray/config.json`

## Installation

### Docker (default)

```powershell
cd C:\path\to\balabolkaBot
Copy-Item .\config\.env.example .\config\.env
# edit config\.env — see Configuration below

# optional: proxy sidecar
Copy-Item .\xray\config.example.json .\xray\config.json
# edit xray\config.json with your VPS/client settings

docker compose build
docker compose up -d
```

Follow logs:

```powershell
docker compose logs -f bot
docker compose logs -f xray      # if proxy sidecar is in use
docker compose logs -f watchdog
```

Stop:

```powershell
docker compose down
```

### Local (without Docker)

```powershell
cd C:\path\to\balabolkaBot
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# copy and fill config\.env first
python bot.py
```

PyTorch installs from the CPU wheel index (`requirements.txt` pins `torch==2.8.0`). First run downloads `v5_5_ru.pt` into the working directory.

## Configuration

Copy `config/.env.example` to `config/.env` and fill in the required values.

### Required

```dotenv
ADMIN_USERNAME=your_telegram_username
API_KEY_TELEGRAM=123456:ABC...
NETWORK_ALARM_DIR=//server/share/folder
SMB_USERNAME=smb_user
SMB_PASSWORD=smb_password
```

Notes:

- `ADMIN_USERNAME` — no `@` prefix. This user is auto-added to the whitelist on first start.
- `NETWORK_ALARM_DIR` — UNC-style path that `smbprotocol` can open. Output file is always `<dir>/alarm.wav`.

### SMB and startup retries

```dotenv
SMB_RETRY_DELAY_SECONDS=10
SMB_RETRY_MAX_ATTEMPTS=-1
```

`-1` means keep retrying SMB registration forever on startup. Set a positive number to fail fast instead.

### Telegram routing (optional)

Leave empty for direct Telegram API access. Set both to route through the compose Xray sidecar:

```dotenv
TELEGRAM_PROXY_URL=http://xray:8080
TELEGRAM_UPDATES_PROXY_URL=http://xray:8080
```

Advanced: custom Bot API endpoints if you run a local Bot API server.

```dotenv
TELEGRAM_BASE_URL=
TELEGRAM_BASE_FILE_URL=
```

### Self-heal settings

The bot process exits on repeated network errors so Docker `restart: unless-stopped` can recover client state:

```dotenv
NETWORK_ERROR_RESTART_THRESHOLD=8
NETWORK_ERROR_RESTART_WINDOW_SECONDS=120
```

Internal polling monitor (enabled by default) also exits if `getUpdates` goes stale:

```dotenv
POLLING_MONITOR_ENABLED=true
POLLING_MONITOR_INTERVAL_SECONDS=20
POLLING_MONITOR_RESTART_THRESHOLD=3
POLLING_MONITOR_STALE_SECONDS=120
POLLING_MONITOR_STARTUP_GRACE_SECONDS=180
```

Watchdog container probes Telegram through the proxy and restarts `xray` + `bot` after repeated failures:

```dotenv
WATCHDOG_ENABLED=true
WATCHDOG_PROXY_URL=http://xray:8080
WATCHDOG_CHECK_URL=
WATCHDOG_INTERVAL_SECONDS=20
WATCHDOG_FAIL_THRESHOLD=4
WATCHDOG_RESTART_COOLDOWN_SECONDS=20
```

`WATCHDOG_CHECK_URL` left empty defaults to `/bot<TOKEN>/getMe` via proxy. Watchdog mounts the Docker socket — treat the host accordingly.

### Xray sidecar

Only needed when Telegram is not reachable directly.

```powershell
Copy-Item .\xray\config.example.json .\xray\config.json
```

Edit `xray/config.json`:

- `outbounds[0].settings.vnext[0].address` — VPS IP or domain
- `outbounds[0].settings.vnext[0].users[0].id` — client UUID from 3X-UI
- `outbounds[0].streamSettings.realitySettings.serverName` — SNI from inbound
- `outbounds[0].streamSettings.realitySettings.publicKey` — REALITY public key
- `outbounds[0].streamSettings.realitySettings.shortId` — shortId for this client

`xray/config.json` is git-ignored. Port defaults to 443; change only if your inbound differs.

## Usage

Bot commands (also visible in the Telegram menu after `/start`):

| command | who | what |
| --- | --- | --- |
| `/start` | anyone | greeting |
| `/help` | anyone | short command list |
| `/ping` | anyone | liveness check |
| `/files` | anyone | list files in `NETWORK_ALARM_DIR` |
| `/tts` | anyone | generate preview audio for all voices; does not write to share |
| `/alarm` | whitelist | mount or remove `alarm.wav` on the share |
| `/cancel` | anyone | abort an active `/tts` or `/alarm` conversation |
| `/whitelist_add` | admin | add `@user` or `user` |
| `/whitelist_remove` | admin | remove a user (admin cannot remove self) |
| `/whitelist_list` | admin | show whitelisted usernames |
| `/logs` | admin | recent audit log entries |

### Text input rules

- Russian Cyrillic only. Latin characters are rejected.
- Put `+` before a vowel to mark stress: `оповещ+ение`, `сист+емы`.
- `/tts` sends one audio file per voice (aidar, baya, kseniya, xenia, eugene).
- `/alarm` follows the same preview step, then you pick a voice to mount.

### `/alarm` flow

**No `alarm.wav` on the share:**

1. `/alarm` → send text
2. Bot sends preview clips for all voices
3. Pick a voice name to mount, or "Изменить текст" / "Отмена"

**`alarm.wav` already exists:**

1. `/alarm` → bot offers "Отключить балаболку" or "Отмена"
2. Confirm to delete the file from the share

Only one `alarm.wav` at a time. To use a different filename, change `get_alarm_path()` in `config/env.py`.

### Whitelist

On first start the admin from `.env` lands in `whitelist.json` (git-ignored, persisted in the container working dir). Non-whitelisted users get a permission message on `/alarm`; the attempt is logged.

## Project Layout

```text
bot.py                  entry point
commands/               Telegram command handlers
services/               TTS, SMB, auth, logging, polling monitor
config/env.py           env loading and alarm path
config/.env             secrets (not in git)
xray/config.json        local proxy config (not in git)
watchdog/recover.sh     proxy health probe and container restart
docker-compose.yml      xray + bot + watchdog
```

More detail on auth, logging, and alarm states: `AUTHENTICATION.md`, `LOGGING.md`, `ALARM_WORKFLOW.md`, `DEPLOYMENT.md`.

## Logs

- Bot stdout/stderr: `docker compose logs -f bot`
- Audit trail: `/logs` command (admin) and log files written by `services/logger.py`
- Xray: `docker compose logs -f xray`
- Watchdog restarts are printed with UTC timestamps in the watchdog container log

## Troubleshooting

- `Missing environment variable: ...` — check `config/.env` keys and that compose `env_file` points to it.
- SMB errors on startup — verify `NETWORK_ALARM_DIR`, credentials, and that the share is reachable from the host/container network.
- `Path does not exist` on `/files` — share path wrong or SMB session not registered yet.
- TTS download fails — container/host needs HTTPS access to `https://models.silero.ai`.
- Telegram timeouts or `NetworkError` spam — enable Xray sidecar, set proxy env vars, confirm `xray/config.json` matches your 3X-UI client.
- Bot keeps restarting — check `NETWORK_ERROR_RESTART_*` and polling monitor thresholds; inspect watchdog log for proxy probe failures.
- `/alarm` says no permission — admin must `/whitelist_add` the user first.
- Watchdog not restarting containers — needs Docker socket mount and runs as root in compose; verify `WATCHDOG_ENABLED=true`.
