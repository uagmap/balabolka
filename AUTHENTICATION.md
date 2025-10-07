# Authentication System

## Overview

The bot uses a whitelist-based authentication system. Only authorized users can interact with the bot, and only the admin can manage the whitelist.

## Setup

### 1. Add Admin Username to .env

Add your Telegram username to the `.env` file:

```env
ADMIN_USERNAME=your_telegram_username
```

**Important:** Do NOT include the `@` symbol. Just use the username itself.

Example:
```env
ADMIN_USERNAME=johndoe
```

### 2. Initial Setup

When the bot starts for the first time:
- The admin username from `.env` will be automatically added to the whitelist
- A `whitelist.json` file will be created

## Usage

### For Admin

As the admin, you have access to special commands to manage the whitelist:

#### Add a user to whitelist
```
/whitelist_add @username
```
or
```
/whitelist_add username
```

#### Remove a user from whitelist
```
/whitelist_remove @username
```
or
```
/whitelist_remove username
```

**Note:** You cannot remove yourself (admin) from the whitelist.

#### List all whitelisted users
```
/whitelist_list
```

### For Regular Users

- Users must be in the whitelist to use any bot commands
- If not whitelisted, they will receive lack of permission message
- Whitelist management commands are hidden from the `/help` menu and only work for the admin

## Security Features

1. **Environment-based admin**: Admin username is stored securely in `.env` file
2. **Persistent whitelist**: User list is stored in `whitelist.json` (git-ignored)
3. **Case-insensitive**: Usernames are normalized (lowercase) for consistent checking
4. **Flexible format**: Works with or without `@` prefix
5. **Admin protection**: Admin cannot be removed from whitelist
6. **Decorator-based**: All commands are protected with `@require_auth` decorator


## Example Workflow

1. Start the bot - admin is automatically whitelisted
2. Admin uses `/whitelist_add @john` to add user "john"
3. User @john can now use the bot
4. Admin uses `/whitelist_list` to see all authorized users
5. Admin uses `/whitelist_remove bob` to revoke access for "bob"



# Authentication Test Plan

## 1. Whitelist Management
### Add User
- [x] Add new user with `@username`
- [x] Add new user without `@`
- [x] Try adding an existing user
- [x] Verify user appears in whitelist

### Remove User
- [x] Remove existing user
- [x] Try removing non-existent user
- [x] Verify user is removed from whitelist

### List Users
- [x] List users when whitelist is empty (should be only admin if in .env, throws error if admin not set)
- [x] List users with multiple users
- [x] Verify output format

## 2. Authentication Decorators
### `@require_auth`
- [x] Access command with whitelisted user
- [x] Can't access command with non-whitelisted user
- [x] Can't access command with no username
- [x] Verify correct error message

### `@require_admin`
- [x] Access admin command with admin user
- [x] Can't access admin command with non-admin user
- [x] Can't access admin command with no username
- [x] Verify correct error message

## 3. Edge Cases
### Username Formatting
- [x] Username with mixed case
- [x] Username with special characters
- [x] Very long usernames?

### Concurrent Access
- [x] Multiple users accessing simultaneously

## 4. Persistence
### Restart Persistence
- [x] Add users
- [x] Restart bot
- [x] Verify users remain in whitelist

## 5. Command Authorization
### Whitelist Commands
- [x] `/whitelist_add` - admin only
- [x] `/whitelist_remove` - admin only
- [x] `/whitelist_list` - admin only

### Regular Commands
- [x] Regular commands with `@require_auth`
- [x] Commands without decorators

## 6. Error Handling
### Invalid Inputs
- [x] Empty username
- [x] Malformed commands

### Permission Denied
- [x] Verify error messages
- [x] Verify command execution stops

