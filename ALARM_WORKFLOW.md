# Alarm Workflow Documentation

## Overview
The `/alarm` command enables users to mount and unmount alarm messages through bot interaction. The workflow ensures only one `alarm.wav` file exists at a time in the network folder.

## User Flow

### Scenario 1: No Alarm Exists
1. User sends `/alarm`
2. Bot prompts for message text (Cyrillic with `+` for accent marks)
3. User sends text (e.g., "Тест сист+емы оповещ+ений!")
4. Bot generates TTS and sends preview audio file
5. Bot presents three options:
   - **Установить** — Mount the alarm to network folder
   - **Изменить текст** — Re-enter text and regenerate
   - **Отмена** — Cancel the operation
6. If user selects "Установить", bot writes file to network folder as `alarm_test.wav`
7. Success confirmation displayed

### Scenario 2: Alarm Already Exists
1. User sends `/alarm`
2. Bot detects existing `alarm_test.wav` in network folder
3. Bot presents two options:
   - **Отключить тревогу** — Delete the alarm file
   - **Отмена** — Cancel the operation
4. If user selects "Отключить тревогу", bot deletes the file
5. Success confirmation displayed

## Technical Details

### File Path
- Currently uses `alarm_test.wav` for testing
- Located in: `NETWORK_ALARM_DIR/alarm_test.wav`
- To switch to production: change `alarm_test.wav` to `alarm.wav` in `get_alarm_path()` function

### Conversation States
- **ALARM_CHECK_STATE** — Handle disable option when alarm exists
- **ALARM_AWAIT_TEXT** — Wait for user's message text input
- **ALARM_VALIDATE** — Wait for user's validation response (mount/regenerate/cancel)

### Context Data
- `alarm_text` — Stores the user's input text
- `alarm_wav` — Stores the generated WAV file bytes

### Cancellation
- `/cancel` command available at any point in the conversation
- Clears all user data and returns to normal mode

## Testing Checklist

- [x] Start bot successfully
- [x] Run `/alarm` when no alarm exists
- [x] Generate TTS with valid Cyrillic text
- [x] Validate and mount alarm file
- [x] Check file exists in network folder
- [x] Run `/alarm` when alarm exists
- [x] Disable existing alarm
- [x] Verify file deleted from network folder
- [x] Test `/cancel` at each conversation state
- [x] Test regeneration flow (Изменить текст)
- [ ] Test error handling (invalid network path, permission issues, etc.)

## Next Steps

1. Change filename from `alarm_test.wav` to `alarm.wav` in production
2. Add user authentication/whitelist
3. Add logging for audit trail?
4. Сonfirmation prompt before deletion?