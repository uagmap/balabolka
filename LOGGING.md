# Activity Logging System

## Overview

The bot logs important activities to a file for audit and monitoring purposes. This helps you track who's using the alarm feature and when.

## What Gets Logged

### 1. **Alarm Mounted** ✅
Logged when a user successfully installs an alarm to the network folder.

**Information captured:**
- Timestamp (ISO format)
- Username
- Full text content of the alarm

**Example log entry:**
```json
{"timestamp": "2025-10-07T15:10:03+03:00", "action": "alarm_mounted", "username": "johndoe", "text": "Добрый день, это оповещение"}
```

### 2. **Alarm Disabled** 🔕
Logged when a user removes/disables an alarm.

**Information captured:**
- Timestamp
- Username and User ID

**Example log entry:**
```json
{"timestamp": "2025-10-07T15:15:20+03:00", "action": "alarm_disabled", "username": "johndoe"}
```

### 3. **Authentication Failures** ⛔ (Optional)
Can be enabled to track unauthorized access attempts.

### 4. **Whitelist Changes** 📝 (Optional)
Can be enabled to track when admin adds/removes users.

## Log File Location

Logs are stored in: `bot_activity.log` (in the project root directory)

**Format:** JSON Lines (`.jsonl`) - each line is a separate JSON object
- Easy to parse and analyze
- Append-only for efficiency
- Human-readable

## Viewing Logs

### Via Telegram (Admin Only)

Use the `/logs` command to view recent activity:

```
/logs          # Shows last 20 entries
/logs 50       # Shows last 50 entries (max 100)
```

The command formats logs in a readable way:
- 🔔 Alarm mounted
- 🔕 Alarm disabled
- ⛔ Auth failures (if enabled)
- ➕/➖ Whitelist changes (if enabled)

### Via File

You can also directly view the `bot_activity.log` file. Each line is a JSON object that can be parsed.


## Privacy & Security

- The log file is **git-ignored** 
- Logs are stored **locally only** on the server
- Only the admin can view logs via the `/logs` command
- .wav files are **NOT** stored in logs (only text content)

## When Logging Happens

✅ **Logged:**
- User successfully mounts alarm (after clicking "Утвердить")
- User disables/removes an existing alarm

❌ **Not Logged:**
- User starts alarm conversation but cancels
- User generates TTS preview but doesn't mount
- Regular commands like /help, /ping, etc.

This ensures logs only capture **meaningful actions**, not exploratory use.

## Log Retention

- Logs are **append-only** and never automatically deleted
- Manually truncate/archive the log file if it gets too large
- Consider setting up log rotation

## Example Use Cases

1. **Audit Trail**: See who's been setting phone announcements
2. **Activity Monitoring**: Track usage patterns
3. **Troubleshooting**: Debug issues by reviewing recent activities
4. **Accountability**: Know who changed what and when


## Notes

- Timestamps are in ISO 8601 format with timezone
- Usernames may be "unknown" if user has no username set
- The logger uses a singleton pattern (one global instance)
