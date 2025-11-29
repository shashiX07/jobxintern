# 👑 Admin Commands Guide

## Quick Access

Send `/admin` in your bot to see all commands.

## Available Commands

### 🔧 Testing & Control

**`/scrape`** - Manually trigger job scraping
- Forces immediate scraping for all user preferences
- Useful for testing or getting fresh jobs
- Example: Just send `/scrape`

**`/notify`** - Send notifications to all users now
- Sends job alerts to all active users immediately
- Bypasses the scheduled notification times
- Example: Just send `/notify`

**`/testjob`** - Add test jobs to database
- Creates 2 sample jobs (Python Dev & Web Dev)
- Useful for testing notifications without waiting for scrape
- Example: Just send `/testjob`

### 📊 Monitoring

**`/stats`** - View bot statistics
- Shows user count, job count, sources, popular domains
- Updated in real-time
- Example: Just send `/stats`

**`/users`** - List all registered users
- Shows up to 20 recent users with their preferences
- Displays username, job type, domains, join date
- Example: Just send `/users`

### 📢 Communication

**`/broadcast <message>`** - Send message to all users
- Broadcasts to all active users
- Shows delivery status (sent/failed)
- Example: `/broadcast New feature added! Check it out.`

### 🗑️ Maintenance

**`/clearjobs`** - Delete old jobs (>7 days)
- Cleans up database
- Keeps only recent jobs
- Example: Just send `/clearjobs`

## Usage Examples

### Test Complete Flow:

```
1. /testjob          # Add test jobs
2. /stats            # Verify jobs added
3. /notify           # Send to users
4. /users            # Check user list
```

### Force Scraping:

```
1. /scrape           # Start scraping now
2. /stats            # Check job count
```

### Broadcast Announcement:

```
/broadcast 🎉 Bot updated! Now scraping every 12 hours. Check /help for commands.
```

## Admin Setup

Your admin ID is set in `.env`:
```
ADMIN_ID=25886208
```

Only this user can use admin commands. Others will see "⛔ Admin access required!"

## Tips

- Use `/scrape` after users complete onboarding to get jobs immediately
- Use `/testjob` + `/notify` to test the notification system
- Use `/stats` regularly to monitor bot health
- Use `/clearjobs` weekly to keep database clean
- Use `/broadcast` sparingly to avoid spam

## Troubleshooting

**"Scheduler not found" error:**
- Restart the bot: `python main.py`

**Scraping returns 0 jobs:**
- Check if users exist: `/users`
- If no users, add via Telegram: `/start`
- Then try `/scrape` again

**Notifications not sending:**
- Check active users: `/users`
- Verify jobs exist: `/stats`
- Try `/testjob` first, then `/notify`

## Security Note

⚠️ Keep your `.env` file secure! It contains:
- Your bot token
- Your admin ID
- Database credentials

Never commit `.env` to git or share it publicly.
