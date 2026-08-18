#!/bin/sh
set -eu

ENABLED="${WATCHDOG_ENABLED:-true}"
PROXY_URL="${WATCHDOG_PROXY_URL:-}"
CHECK_URL="${WATCHDOG_CHECK_URL:-}"
INTERVAL_SECONDS="${WATCHDOG_INTERVAL_SECONDS:-20}"
FAIL_THRESHOLD="${WATCHDOG_FAIL_THRESHOLD:-4}"
COOLDOWN_SECONDS="${WATCHDOG_RESTART_COOLDOWN_SECONDS:-20}"
XRAY_CONTAINER="${WATCHDOG_XRAY_CONTAINER:-balabolka-xray}"
BOT_CONTAINER="${WATCHDOG_BOT_CONTAINER:-balabolka-bot}"
BOT_TOKEN="${API_KEY_TELEGRAM:-}"

BOT_LOG_ERROR_THRESHOLD=2
BOT_LOG_ERROR_PATTERN="telegram.error.NetworkError|httpx.RemoteProtocolError|httpx.ConnectError|httpcore.RemoteProtocolError|httpcore.ConnectError"

if [ "$ENABLED" != "true" ]; then
  echo "[watchdog] disabled (WATCHDOG_ENABLED=$ENABLED)"
  while true; do
    sleep 3600
  done
fi

if [ -n "$CHECK_URL" ]; then
  PROBE_URL="$CHECK_URL"
else
  if [ -n "$BOT_TOKEN" ]; then
    PROBE_URL="https://api.telegram.org/bot${BOT_TOKEN}/getMe"
  else
    PROBE_URL="https://api.telegram.org"
  fi
fi

PROBE_URL_DISPLAY="$PROBE_URL"
if echo "$PROBE_URL" | grep -q "/bot"; then
  PROBE_URL_DISPLAY="$(echo "$PROBE_URL" | sed -E 's#(https://api.telegram.org/bot)[^/]+/#\1<redacted>/#')"
fi

echo "[watchdog] started: proxy=$PROXY_URL probe_url=$PROBE_URL_DISPLAY interval=${INTERVAL_SECONDS}s fail_threshold=$FAIL_THRESHOLD log_threshold=$BOT_LOG_ERROR_THRESHOLD"

failed_checks=0
failed_log_windows=0
last_log_since="$(date +%s)"
recent_bot_logs=""

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

probe() {
  if [ -n "$PROXY_URL" ]; then
    curl -fsS --max-time 12 -x "$PROXY_URL" "$PROBE_URL"
  else
    curl -fsS --max-time 12 "$PROBE_URL"
  fi
}

restart_container() {
  container_name="$1"
  status_code="$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 --unix-socket /var/run/docker.sock \
    -X POST "http://localhost/v1.41/containers/${container_name}/restart?t=5" || true)"
  if [ "$status_code" = "204" ]; then
    echo "[watchdog] restarted container: ${container_name}"
    return 0
  fi
  echo "[watchdog] failed to restart container ${container_name} (docker API status: ${status_code:-none})"
  return 1
}

collect_recent_bot_logs() {
  overlap_since="$last_log_since"
  if [ "$overlap_since" -gt 2 ]; then
    overlap_since=$((overlap_since - 2))
  fi
  current_time="$(date +%s)"
  recent_bot_logs="$(curl -sS --max-time 10 --unix-socket /var/run/docker.sock \
    "http://localhost/v1.41/containers/${BOT_CONTAINER}/logs?stdout=1&stderr=1&since=${overlap_since}&tail=200" || true)"
  last_log_since="$current_time"
}

has_recent_bot_network_errors() {
  if [ -z "$recent_bot_logs" ]; then
    return 1
  fi
  if echo "$recent_bot_logs" | grep -Eiq "$BOT_LOG_ERROR_PATTERN"; then
    return 0
  fi
  return 1
}

while true; do
  response="$(probe 2>/dev/null || true)"
  probe_ok="false"

  if [ -n "$BOT_TOKEN" ] || echo "$PROBE_URL" | grep -q "/bot"; then
    if echo "$response" | grep -q '"ok":true'; then
      probe_ok="true"
    fi
  else
    if [ -n "$response" ]; then
      probe_ok="true"
    fi
  fi

  if [ "$probe_ok" = "true" ]; then
    if [ "$failed_checks" -gt 0 ]; then
      echo "[watchdog] probe recovered after ${failed_checks} failed checks"
    fi
    failed_checks=0
  else
    failed_checks=$((failed_checks + 1))
    echo "[watchdog] probe failed ($failed_checks/$FAIL_THRESHOLD)"
  fi

  collect_recent_bot_logs

  if has_recent_bot_network_errors; then
    failed_log_windows=$((failed_log_windows + 1))
    echo "[watchdog] bot network errors detected in logs ($failed_log_windows/$BOT_LOG_ERROR_THRESHOLD)"
  else
    if [ "$failed_log_windows" -gt 0 ]; then
      echo "[watchdog] bot log errors recovered after ${failed_log_windows} failed windows"
    fi
    failed_log_windows=0
  fi

  echo "[watchdog] status $(timestamp) probe_ok=$probe_ok probe_failures=$failed_checks log_failures=$failed_log_windows"

  if [ "$failed_checks" -ge "$FAIL_THRESHOLD" ] || [ "$failed_log_windows" -ge "$BOT_LOG_ERROR_THRESHOLD" ]; then
    echo "[watchdog] restarting containers: $XRAY_CONTAINER, $BOT_CONTAINER (probe_failures=$failed_checks, log_failures=$failed_log_windows)"
    restart_container "$XRAY_CONTAINER" || true
    restart_container "$BOT_CONTAINER" || true
    failed_checks=0
    failed_log_windows=0
    last_log_since="$(date +%s)"
    sleep "$COOLDOWN_SECONDS"
  else
    sleep "$INTERVAL_SECONDS"
  fi
done
