## Deployment Guide

This guide explains how to containerize and run the Telegram bot locally and on a remote server using Docker.

### 1) Prerequisites
- Docker Engine and Docker Compose
- Outbound internet access from the host
- SMB share reachability from the host/container for alarm files

### 2) Project Files
- `Dockerfile` (builds the image)
- `docker-compose.yml` (runs the image with environment variables)
- `.dockerignore` (keeps image small)

### 3) Environment Variables (.env)
Create a file named `.env` in the project root next to `docker-compose.yml` with the following keys:

```
API_KEY_TELEGRAM=YOUR_TELEGRAM_BOT_TOKEN
NETWORK_ALARM_DIR=//server/share/path
SMB_USERNAME=your-smb-username
SMB_PASSWORD=your-smb-password

```

Notes:
- `NETWORK_ALARM_DIR` must be an SMB UNC-like path that `smbprotocol` can access (e.g. `//server/share/folder`).
- The bot downloads a TTS model on first use. Make sure the container can reach `https://models.silero.ai`.

### 4) Build the image
From the project root (where `Dockerfile` is located):

```bash
docker compose build
```

### 5) Run the bot

```bash
docker compose up -d
```

Logs:
```bash
docker compose logs -f
```

Stop:
```bash
docker compose down
```

### 6) Optional: Persisting the TTS model file
The model `v4_ru.pt` is downloaded into the container filesystem. To avoid re-downloading across deploys, a volume is mounted:

```yaml
# In docker-compose.yml
services:
  bot:
    volumes:
      - tts-cache:/app
volumes:
  tts-cache:
```

This will persist `/app/v4_ru.pt` across container recreations.
