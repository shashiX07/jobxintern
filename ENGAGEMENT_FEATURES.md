# 🎉 Engagement Features Added!

## ✨ What's New

### ⚡ Faster Updates
- **Scraping**: Every **6 hours** (was 12 hours)
- **Notifications**: **4 times daily** at 8AM, 12PM, 4PM, 8PM (was 2 times)

### 📊 User Engagement Features

#### 1. **My Stats** Button
Shows users:
- Account age & user ID
- Their preferences (job type, work mode, domains)
- Total notifications received
- Scraping & notification schedule

#### 2. **Share Bot** Button
- Easy share message with bot link
- Copyable text for WhatsApp/Telegram
- Encourages viral growth

#### 3. **Support Us** Button ☕
- Displays your UPI ID for donations
- Shows how donations help
- Customizable donation message
- Users can copy UPI ID easily

### 🎯 Enhanced User Experience
- More engaging main menu (7 buttons instead of 4)
- Tips when no jobs found
- Updated help text with new timings
- Better stats tracking

## 🔧 Configuration

**In your `.env` file**, add your UPI ID:
```env
DONATION_UPI=yourname@paytm
```

Replace `yourname@paytm` with your actual UPI ID (e.g., `name@phonepe`, `9876543210@paytm`, etc.)

## 📱 New Menu Structure

```
🔍 View Jobs          👤 My Account
📊 My Stats           💡 Share Bot
⚙️ Change Preferences  ☕ Support Us
         ℹ️ Help
```

## 🚀 Deploy on Linux Server

```bash
# Pull latest changes
git pull

# Update .env with your UPI ID
nano .env

# Restart bot
python main.py
```

## 📊 Notification Schedule

| Time  | Action           |
|-------|------------------|
| 08:00 | Send notifications |
| 12:00 | Send notifications |
| 16:00 | Send notifications |
| 20:00 | Send notifications |

Jobs are scraped every 6 hours to keep content fresh!

## 💡 Tips for More Engagement

1. **Set a real UPI ID** in `.env` for donations
2. **Share the bot** on social media to grow users
3. **Monitor stats** with `/stats` admin command
4. **Respond to user feedback** via broadcast feature

---

**All changes pushed to GitHub!** 🎉
Pull on your Linux server and restart the bot.
