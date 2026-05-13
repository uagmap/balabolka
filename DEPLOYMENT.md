## Deployment Guide

This guide explains how to containerize and run the Telegram bot locally and on a remote server using Docker.

### 1) Prerequisites
- Docker Engine and Docker Compose
- Outbound internet access from the host
- SMB share reachability from the host/container for alarm files

### 2) Project Files
- `Dockerfile` (builds the image)
- `docker-compose.yml` (runs the image with environment variables)
- `.dockerignore` (ignore files when building image)

### 3) Environment Variables (config/.env)
Create a file named `config/.env` with the following keys:

```
ADMIN_USERNAME=YOUR_ADMIN_USERNAME
API_KEY_TELEGRAM=YOUR_TELEGRAM_BOT_TOKEN
NETWORK_ALARM_DIR=//server/share/path
SMB_USERNAME=your-smb-username
SMB_PASSWORD=your-smb-password
SMB_RETRY_DELAY_SECONDS=10
SMB_RETRY_MAX_ATTEMPTS=-1
NETWORK_ERROR_RESTART_THRESHOLD=8
NETWORK_ERROR_RESTART_WINDOW_SECONDS=120

# Optional: route Telegram traffic through proxy/VPN egress
# Leave empty for direct connection; set to http://xray:8080 to use sidecar tunnel
TELEGRAM_PROXY_URL=
TELEGRAM_UPDATES_PROXY_URL=

# Optional: custom Bot API endpoint (advanced)
TELEGRAM_BASE_URL=
TELEGRAM_BASE_FILE_URL=

# Optional bot-side monitor that exits process when polling appears stuck.
POLLING_MONITOR_ENABLED=true
POLLING_MONITOR_INTERVAL_SECONDS=20
POLLING_MONITOR_RESTART_THRESHOLD=3

# Optional watchdog auto-restarts xray+bot when Telegram probe fails repeatedly.
WATCHDOG_ENABLED=true
WATCHDOG_PROXY_URL=http://xray:8080
# Leave empty to auto-probe /bot<TOKEN>/getMe via proxy
WATCHDOG_CHECK_URL=
WATCHDOG_INTERVAL_SECONDS=20
WATCHDOG_FAIL_THRESHOLD=4
WATCHDOG_RESTART_COOLDOWN_SECONDS=20

```

Notes:
- `NETWORK_ALARM_DIR` must be an SMB UNC-like path that `smbprotocol` can access (e.g. `//server/share/folder`).
- The bot downloads a TTS model on first use. Make sure the container can reach `https://models.silero.ai`.
- `SMB_RETRY_MAX_ATTEMPTS=-1` means keep retrying SMB registration forever on startup.
- Network polling errors are counted in a rolling window; if threshold is reached the process exits so Docker restart policy can self-heal client state.
- If `TELEGRAM_PROXY_URL` / `TELEGRAM_UPDATES_PROXY_URL` are empty, bot goes directly to Telegram API.
- If they are set to `http://xray:8080`, bot routes Telegram API calls through the sidecar tunnel.
- Long-poll request timeouts are now fixed in code to stable defaults for xray (`connect=8s`, `read=25s`, `write=8s`, `pool=5s`, polling timeout `10s`).
- `watchdog` checks Telegram reachability and restarts `xray` + `bot` if proxy path stays broken for several checks.
- `watchdog` mounts Docker socket to call restart API. Treat it as privileged infrastructure access.
- `watchdog` runs as root to access Docker socket on Linux containers.
- `watchdog` also scans recent bot logs for repeated Telegram/httpx network errors.

### 4) Configure Xray sidecar for VLESS REALITY

The compose setup includes an `xray` container that provides an HTTP proxy on `http://xray:8080` for Telegram API calls.
You can keep this container running all the time, or ignore it when direct mode is enough.

1. Copy the template config:

```bash
cp xray/config.example.json xray/config.json
```

PowerShell equivalent:
```powershell
Copy-Item .\xray\config.example.json .\xray\config.json
```

2. Edit `xray/config.json` and fill:
- `outbounds[0].settings.vnext[0].address` -> your VPS IP or domain
- `outbounds[0].settings.vnext[0].users[0].id` -> client UUID from 3X-UI
- `outbounds[0].streamSettings.realitySettings.serverName` -> SNI from 3X-UI
- `outbounds[0].streamSettings.realitySettings.publicKey` -> REALITY public key
- `outbounds[0].streamSettings.realitySettings.shortId` -> shortId for that client
- `outbounds[0].settings.vnext[0].users[0].flow` -> usually empty string for standard VLESS REALITY TCP

3. Keep port `443` unless your inbound uses another port.

4. `xray/config.json` is ignored by git so private keys and IDs stay local.
5. For REALITY, `serverName` must match one of the server-side `realitySettings.serverNames`.
6. `shortId` must be one of server-side `realitySettings.shortIds`. If unsure, use the one from exported client link for this specific bot client.

### 5) Build the image
From the project root (where `Dockerfile` is located):

```bash
docker compose build
```

### 6) Run the bot

```bash
docker compose up -d
```

View logs:
```bash
docker compose logs -f
```

Check sidecar logs:
```bash
docker compose logs -f xray
```

Check watchdog logs:
```bash
docker compose logs -f watchdog
```

Stop:
```bash
docker compose down
```
