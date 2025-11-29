# 🚀 Free Deployment Guide

Complete guide to deploy your Job & Internship Telegram Bot for **FREE** using various hosting platforms.

## 📋 Table of Contents

1. [Preparation](#preparation)
2. [Free MySQL Database](#free-mysql-database)
3. [Free Redis Instance](#free-redis-instance)
4. [Bot Deployment Options](#bot-deployment-options)
5. [Final Configuration](#final-configuration)
6. [Monitoring](#monitoring)

---

## 🎯 Preparation

### 1. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the **Bot Token** (you'll need this)
5. Send `/setcommands` and add:
   ```
   start - Start the bot and setup preferences
   help - Show help information
   ```

### 2. Get Your User ID

1. Search for [@userinfobot](https://t.me/userinfobot)
2. Send any message
3. Copy your **User ID**

### 3. Get Channel IDs (Optional)

1. Create your Telegram channels
2. Add [@userinfobot](https://t.me/userinfobot) to each channel as admin
3. Send a message in the channel
4. Bot will show the channel ID (will be negative number like `-1001234567890`)
5. Remove the bot from channels after getting IDs

---

## 🗄️ Free MySQL Database

### Option 1: Railway.app (Recommended)

**Pros**: 500 hours free/month, easy setup, good performance

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Provision MySQL"
4. Click on MySQL service → "Variables" tab
5. Copy these values:
   - `MYSQLHOST` → Your MYSQL_HOST
   - `MYSQLPORT` → Your MYSQL_PORT
   - `MYSQLUSER` → Your MYSQL_USER
   - `MYSQLPASSWORD` → Your MYSQL_PASSWORD
   - `MYSQLDATABASE` → Your MYSQL_DATABASE

### Option 2: db4free.net

**Pros**: Completely free, unlimited time

1. Go to [db4free.net](https://www.db4free.net)
2. Sign up for a free account
3. Fill in the form:
   - Database Name (your choice)
   - Username (your choice)
   - Password (your choice)
4. Verify email
5. Use these details:
   ```
   MYSQL_HOST=db4free.net
   MYSQL_PORT=3306
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=your_database_name
   ```

### Option 3: FreeSQLDatabase

1. Go to [freesqldatabase.com](https://www.freesqldatabase.com)
2. Click "Create Free MySQL Database"
3. Fill in the form
4. You'll receive connection details via email

**Note**: For production, consider paid options for better reliability.

---

## ⚡ Free Redis Instance

### Option 1: Redis Cloud (Recommended)

**Pros**: 30MB free forever, reliable, fast

1. Go to [redis.com/try-free](https://redis.com/try-free/)
2. Sign up for free account
3. Create a new subscription (select Free 30MB plan)
4. Create a database
5. Go to "Configuration" tab
6. Copy:
   - **Public endpoint** (format: `redis-xxxxx.cloud.redislabs.com:12345`)
   - Split into `REDIS_HOST` and `REDIS_PORT`
7. Copy the **Default user password**

Update `.env`:
```env
REDIS_HOST=redis-xxxxx.cloud.redislabs.com
REDIS_PORT=12345
REDIS_PASSWORD=your_password
```

Then update `config.py`:
```python
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None)
}
```

### Option 2: Upstash

**Pros**: 10,000 commands/day free, serverless

1. Go to [upstash.com](https://upstash.com)
2. Sign up with GitHub
3. Create Redis database
4. Copy connection details
5. Use REST API or native connection

---

## 🤖 Bot Deployment Options

### Option 1: Render.com (Recommended for 24/7)

**Pros**: Free tier, 750 hours/month, automatic deploys

#### Step-by-Step:

1. **Prepare Repository**
   ```bash
   # Initialize git if not already
   git init
   git add .
   git commit -m "Initial commit"
   
   # Create GitHub repository and push
   git remote add origin https://github.com/yourusername/job-bot.git
   git branch -M main
   git push -u origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

3. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name**: job-bot
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt && playwright install chromium`
     - **Start Command**: `python main.py`

4. **Add Environment Variables**
   - Go to "Environment" tab
   - Add all variables from `.env`:
     ```
     BOT_TOKEN=your_token
     ADMIN_ID=your_id
     REQUIRED_CHANNELS=-1001234567890
     MYSQL_HOST=your_mysql_host
     MYSQL_PORT=3306
     MYSQL_USER=your_user
     MYSQL_PASSWORD=your_password
     MYSQL_DATABASE=your_db
     REDIS_HOST=your_redis_host
     REDIS_PORT=6379
     REDIS_DB=0
     SCRAPE_INTERVAL_HOURS=12
     NOTIFICATION_TIMES=09:00,18:00
     ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Bot will start automatically!

### Option 2: Railway.app

**Pros**: Easy setup, same place as MySQL

1. Go to your Railway project
2. Click "New" → "GitHub Repo"
3. Connect repository
4. Railway auto-detects Python
5. Add environment variables in "Variables" tab
6. Add start command: `python main.py`
7. Deploy!

### Option 3: PythonAnywhere (Free with limitations)

**Pros**: Free tier available, easy Python hosting

**Cons**: No always-on for free tier, needs manual restart

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to "Consoles" → Start bash console
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/job-bot.git
   cd job-bot
   pip install -r requirements.txt
   playwright install chromium
   ```
4. Create `.env` file with your credentials
5. In "Web" tab, create new web app
6. Set working directory
7. Start with: `python main.py`

**Note**: Free tier sleeps after inactivity. Not suitable for 24/7 bots.

### Option 4: Heroku (Limited Free)

**Note**: Heroku ended free tier in November 2022, but includes credits for students.

### Option 5: Google Cloud Run (Best for Production)

**Pros**: Free tier with generous limits

1. Install Google Cloud CLI
2. Create Dockerfile:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   RUN playwright install chromium
   RUN playwright install-deps
   
   COPY . .
   
   CMD ["python", "main.py"]
   ```
3. Deploy:
   ```bash
   gcloud run deploy job-bot --source .
   ```

### Option 6: VPS (Free Trial)

Many providers offer free trials:
- **Oracle Cloud**: Always free tier (2 VMs)
- **DigitalOcean**: $200 credit for 60 days
- **AWS EC2**: 12 months free tier
- **Google Cloud**: $300 credit for 90 days
- **Azure**: $200 credit for 30 days

#### Setup on Ubuntu VPS:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y
sudo apt install mysql-server redis-server -y

# Clone repository
cd /home
git clone https://github.com/yourusername/job-bot.git
cd job-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# Create .env file
nano .env
# (paste your configuration)

# Setup MySQL
sudo mysql
CREATE DATABASE job_bot;
CREATE USER 'botuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON job_bot.* TO 'botuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Run bot with systemd (for auto-restart)
sudo nano /etc/systemd/system/jobbot.service
```

Add this content:
```ini
[Unit]
Description=Job Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/job-bot
Environment="PATH=/home/job-bot/venv/bin"
ExecStart=/home/job-bot/venv/bin/python /home/job-bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start jobbot
sudo systemctl enable jobbot
sudo systemctl status jobbot
```

---

## ⚙️ Final Configuration

### 1. Update Channel Links in keyboards.py

Edit `keyboards.py`:

```python
def get_channels_keyboard(channels):
    """Check channels keyboard"""
    keyboard = []
    # Replace with your actual channel links
    channel_links = {
        -1001234567890: "https://t.me/yourchannel1",
        -1001234567891: "https://t.me/yourchannel2"
    }
    
    for channel_id in channels:
        keyboard.append([InlineKeyboardButton(
            f"Join Channel",
            url=channel_links.get(channel_id, "https://t.me/yourchannel")
        )])
    keyboard.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")])
    return InlineKeyboardMarkup(keyboard)
```

### 2. Test Bot

1. Start a chat with your bot on Telegram
2. Send `/start`
3. Complete onboarding
4. Check logs for errors

### 3. Monitor First Scraping

Scraping starts immediately on first run. Check logs:

```bash
# On Render/Railway: Check logs in dashboard
# On VPS: 
tail -f bot.log
```

---

## 📊 Monitoring

### Check Bot Status

**On Render/Railway:**
- View logs in dashboard
- Check "Events" for deployments

**On VPS:**
```bash
sudo systemctl status jobbot
tail -f /home/job-bot/bot.log
```

### Monitor MySQL

```bash
mysql -h your_host -u your_user -p
USE job_bot;
SELECT COUNT(*) FROM jobs;
SELECT COUNT(*) FROM users;
```

### Monitor Redis

```bash
redis-cli -h your_host -p your_port -a your_password
INFO
DBSIZE
```

---

## 🔧 Troubleshooting

### Bot doesn't respond

1. Check bot token is correct
2. Verify environment variables set properly
3. Check logs for errors
4. Ensure MySQL and Redis are accessible

### Scraping not working

1. Check internet connectivity
2. Verify Playwright is installed
3. Increase timeout values in scraper.py
4. Check for IP blocks (use proxies if needed)

### Database connection failed

1. Test connection manually
2. Check firewall rules
3. Verify credentials
4. Ensure database exists

### Out of memory

1. Reduce scraping frequency
2. Limit concurrent scraping
3. Clear old jobs from database
4. Upgrade to paid tier

---

## 🎉 Deployment Checklist

- [ ] Bot token obtained from BotFather
- [ ] MySQL database created and accessible
- [ ] Redis instance created and accessible
- [ ] `.env` file configured with all credentials
- [ ] Repository pushed to GitHub
- [ ] Deployment platform chosen
- [ ] Environment variables set on platform
- [ ] Bot deployed and running
- [ ] First scraping completed
- [ ] Test user onboarding works
- [ ] Notifications sending correctly
- [ ] Monitoring setup
- [ ] Logs accessible

---

## 💡 Tips for Free Tier

1. **Optimize Scraping**:
   - Don't scrape too frequently (12-24 hours is fine)
   - Limit max jobs per domain
   - Use Redis caching effectively

2. **Database Management**:
   - Regularly delete old jobs (>7 days)
   - Remove inactive users
   - Index frequently queried columns

3. **Resource Management**:
   - Monitor memory usage
   - Use lightweight scraping
   - Implement rate limiting

4. **Reliability**:
   - Set up health checks
   - Enable auto-restart
   - Monitor logs daily

---

## 🚀 Going to Production

When you outgrow free tier:

1. **Upgrade Database**: Move to managed MySQL (AWS RDS, DigitalOcean, etc.)
2. **Scale Redis**: Upgrade Redis Cloud plan
3. **Bot Hosting**: Use dedicated VPS or container service
4. **Add Features**:
   - Web dashboard
   - Analytics
   - Premium features
   - Payment integration

---

## 📞 Need Help?

- Check logs first (90% of issues are there)
- Verify all environment variables
- Test database connectivity
- Ensure Redis is accessible
- Review deployment platform docs

---

**Remember**: Free tiers have limitations. For a production bot with many users, consider upgrading to paid services for better reliability and performance.

Good luck with your deployment! 🎉
