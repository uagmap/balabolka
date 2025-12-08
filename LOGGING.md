# Activity Logging System

## Overview

The bot logs important activities to a file for audit and monitoring purposes. This helps track who's using the alarm feature and when.

## What Gets Logged

### 1. **Alarm Mounted** ✅
Logged when a user successfully installs an alarm to the network folder.

**Information captured:**
- Timestamp
- Username
- Full text content of the alarm

### 2. **Alarm Disabled** 🔕
Logged when a user removes/disables an alarm.

**Information captured:**
- Timestamp
- Username and User ID

### 3. **Authentication Failures** ⛔
Track unauthorized access attempts.

## Log File Location

Logs are stored in: `activity.log` (in the project root directory) with daily rollover for a month.

**Format:** JSON Lines (`.jsonl`) - each line is a separate JSON object
- Easy to parse and analyze
- Append-only for efficiency
- Human-readable

## Viewing Logs

### Via Telegram (Admin Only)

Use the `/logs` command to view recent activity. The command assimilates all the log files into one temp file to be sent as a document. That way all the logs can be viewed directly from telegram without having to go into project folder.

### Via File

You can also directly view the log files in project directory. Each line is a JSON object that can be parsed.


## Privacy & Security

- The log file is **git-ignored** 
- Logs are stored **locally only** on the server
- Only the admin can view logs via the `/logs` command

## When Logging Happens

✅ **Logged:**
- User successfully mounts alarm
- User disables/removes an existing alarm
- Unauthorized user tries ot access @require_auth command

❌ **Not Logged:**
- User starts alarm conversation but cancels
- User generates TTS but doesn't mount
- Regular commands like /help, /ping, etc.

This ensures logs only capture **meaningful actions**, not exploratory use.


## Example Use Cases

1. **Audit Trail**: See who's been setting phone announcements
2. **Activity Monitoring**: Track usage patterns
3. **Troubleshooting**: Debug issues by reviewing recent activities


## Notes

- Timestamps are in ISO 8601 format with timezone
- Usernames may be "unknown" if user has no username set
- The logger uses a singleton pattern (one global instance)