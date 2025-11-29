# 🤖 Job & Internship Telegram Bot

A smart Telegram bot that helps users find jobs and internships by scraping LinkedIn and Internshala based on personalized preferences. Features automated notifications, channel verification, and a user-friendly onboarding process.

## ✨ Features

- 🔐 **Channel Verification**: Users must join required channels before using the bot
- 📝 **Smooth Onboarding**: Interactive preference selection with custom keyboards
- 🎯 **Personalized Matching**: Choose job type, work mode, and up to 3 domains
- 🔍 **Multi-Source Scraping**: Automated scraping from LinkedIn and Internshala
- 📊 **Smart Caching**: Redis-based caching for optimal performance
- 🔔 **Automated Notifications**: Receive job alerts twice daily
- 💾 **Persistent Storage**: MySQL database for user preferences and jobs
- 🚫 **Anti-Detection**: Uses Playwright for undetected web scraping
- 📱 **User-Friendly Interface**: Custom keyboards and inline buttons

## 🏗️ Architecture

```
bot1/
├── main.py              # Entry point - starts bot and scheduler
├── bot.py               # Telegram bot handlers and logic
├── scheduler.py         # Periodic scraping and notifications
├── scraper.py           # Web scraping (LinkedIn & Internshala)
├── database.py          # MySQL database operations
├── cache.py             # Redis caching layer
├── keyboards.py         # Custom keyboard layouts
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Example environment configuration
└── .gitignore          # Git ignore rules
```

## 📋 Prerequisites

- Python 3.9 or higher
- MySQL 8.0 or higher
- Redis 6.0 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd d:\BOTS\bot1
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Playwright

```bash
playwright install chromium
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id

# Get channel IDs by forwarding a message from the channel to @userinfobot
REQUIRED_CHANNELS=-1001234567890,-1001234567891

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=job_bot

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

SCRAPE_INTERVAL_HOURS=12
NOTIFICATION_TIMES=09:00,18:00
```

### 4. Setup Database

Make sure MySQL is running, then the bot will automatically create tables on first run.

```bash
# Start MySQL (if not running)
# Windows: net start MySQL80
# Linux: sudo systemctl start mysql
```

### 5. Start Redis

```bash
# Windows: redis-server
# Linux: sudo systemctl start redis
```

### 6. Run the Bot

```bash
python main.py
```

## 💡 Usage

### For Users

1. **Start Bot**: Send `/start` to the bot
2. **Join Channels**: Click to join required channels
3. **Complete Onboarding**:
   - Choose Job or Internship
   - Select work mode (Remote/Onsite/Hybrid)
   - Pick up to 3 domains
4. **Receive Notifications**: Get job alerts twice daily
5. **Browse Jobs**: Use menu buttons to explore opportunities

### Bot Commands

- `/start` - Start bot and setup preferences
- `/help` - Show help information

### Menu Options

- 🔍 **View Jobs** - Browse matching jobs immediately
- 👤 **My Account** - View account details
- ⚙️ **Change Preferences** - Update your preferences
- ℹ️ **Help** - Get help information

## 🎯 Supported Domains

- Python Developer
- Web Development
- Data Science
- Machine Learning
- Android Development
- iOS Development
- DevOps
- Digital Marketing
- UI/UX Design
- Content Writing

## 🔧 Configuration

### Scraping Interval

Change `SCRAPE_INTERVAL_HOURS` in `.env` (default: 12 hours)

### Notification Times

Modify `NOTIFICATION_TIMES` in `.env` (format: `HH:MM,HH:MM`)

### Add More Domains

Edit `DOMAINS` list in `config.py`

### Channel Requirements

Add/remove channel IDs in `REQUIRED_CHANNELS` (comma-separated)

## 📊 Database Schema

### Tables

- **users**: User information and preferences
- **user_domains**: Many-to-many relationship for user domains
- **jobs**: Scraped job listings
- **sent_notifications**: Track sent notifications to avoid duplicates

## 🛡️ Anti-Detection Features

- Playwright with Chromium for modern scraping
- Random delays between requests
- Realistic user agents
- Headless browser mode
- Rate limiting built-in

## 📝 Logs

Logs are saved to `bot.log` with rotation. Monitor for errors:

```bash
tail -f bot.log
```

## ⚠️ Troubleshooting

### Bot doesn't start
- Check `.env` file is configured correctly
- Verify MySQL and Redis are running
- Ensure BOT_TOKEN is valid

### No jobs appearing
- Wait for first scraping cycle (runs immediately on start)
- Check logs for scraping errors
- Verify internet connection

### Database errors
- Ensure MySQL user has proper permissions
- Check database exists: `CREATE DATABASE job_bot;`

### Redis connection failed
- Start Redis service
- Check Redis port (default: 6379)

## 🔐 Security Notes

- Never commit `.env` file
- Keep BOT_TOKEN secret
- Use strong MySQL passwords
- Restrict database user permissions
- Enable Redis authentication in production

## 📈 Performance Tips

- Adjust `SCRAPE_INTERVAL_HOURS` based on needs
- Use Redis caching to reduce database load
- Limit `max_jobs` in scraper for faster execution
- Monitor logs for bottlenecks

## 🌟 Features in Detail

### Channel Verification
Users must join specified Telegram channels before accessing the bot. This helps build community and ensures engaged users.

### Smart Onboarding
Interactive flow with inline buttons makes preference selection intuitive. Users can see their selections in real-time.

### Intelligent Matching
Bot matches jobs based on:
- Job type (Job/Internship)
- Work mode (Remote/Onsite/Hybrid with flexible matching)
- Selected domains (up to 3)

### Automated Scraping
- Runs every 12 hours (configurable)
- Scrapes LinkedIn and Internshala
- Stores unique jobs only (no duplicates)
- Handles errors gracefully

### Notification System
- Sends alerts at configured times
- Shows 3-4 matching jobs per notification
- Tracks sent notifications to avoid duplicates
- Interactive job cards with action buttons

## 🤝 Contributing

This bot is designed to be simple and maintainable. Feel free to fork and customize for your needs.

## 📄 License

Free to use for personal and educational purposes.

## 🆘 Support

For issues or questions, check the logs first. Most problems are related to:
1. Missing environment variables
2. Database/Redis not running
3. Invalid bot token
4. Network/scraping issues

## 🎉 Acknowledgments

- python-telegram-bot for the amazing bot framework
- Playwright for reliable web scraping
- Redis for fast caching
- MySQL for robust data storage

---

Made with ❤️ for job seekers everywhere!
