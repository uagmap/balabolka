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

- Users must be in the whitelist to use alarm bot commands
- If not whitelisted, they will receive lack of permission message that will also be logged
- Whitelist management commands are hidden from the `/help` menu and only work for the admin

## Security Features

1. **Environment-based admin**: Admin username is stored securely in `.env` file
2. **Persistent whitelist**: User list is stored in `whitelist.json` (git-ignored)
3. **Case-insensitive**: Usernames are normalized (lowercase) for consistent checking
4. **Flexible format**: Works with or without `@` prefix
5. **Admin protection**: Admin cannot be removed from whitelist
6. **Decorator-based**: Commands can be protected with `@require_auth` decorator


## Example Workflow

1. Start the bot - admin is automatically whitelisted
2. Admin uses `/whitelist_add @john` to add user "john"
3. User @john can now use the protected commands
4. Admin uses `/whitelist_list` to see all authorized users
5. Admin uses `/whitelist_remove bob` to revoke access for "bob"