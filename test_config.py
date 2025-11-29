#!/usr/bin/env python3
"""
Test script to verify your bot configuration before running main.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Checking Bot Configuration...\n")

# Check .env file
print("1️⃣ Checking .env file...")
if not os.path.exists('.env'):
    print("   ❌ .env file not found!")
    print("   → Copy .env.example to .env and fill in your credentials")
    exit(1)
else:
    print("   ✅ .env file found")

# Check bot token
print("\n2️⃣ Checking Telegram Bot Token...")
bot_token = os.getenv('BOT_TOKEN')
if not bot_token or bot_token == 'your_telegram_bot_token_here':
    print("   ❌ BOT_TOKEN not configured!")
    print("   → Get token from @BotFather on Telegram")
    print("   → Add it to .env file: BOT_TOKEN=your_token_here")
    exit(1)
else:
    print(f"   ✅ Bot token configured: {bot_token[:10]}...")

# Check admin ID
print("\n3️⃣ Checking Admin ID...")
admin_id = os.getenv('ADMIN_ID')
if not admin_id or admin_id == '123456789':
    print("   ⚠️  ADMIN_ID using default value")
    print("   → Get your ID from @userinfobot on Telegram")
    print("   → Update .env file: ADMIN_ID=your_user_id")
else:
    print(f"   ✅ Admin ID configured: {admin_id}")

# Check MySQL configuration
print("\n4️⃣ Checking MySQL Configuration...")
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_user = os.getenv('MYSQL_USER', 'root')
mysql_password = os.getenv('MYSQL_PASSWORD', '')
mysql_database = os.getenv('MYSQL_DATABASE', 'job_bot')

print(f"   Host: {mysql_host}")
print(f"   User: {mysql_user}")
print(f"   Database: {mysql_database}")

# Try to connect to MySQL
try:
    import mysql.connector
    print("\n   Testing MySQL connection...")
    connection = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password
    )
    print("   ✅ MySQL connection successful!")
    
    # Check if database exists
    cursor = connection.cursor()
    cursor.execute(f"SHOW DATABASES LIKE '{mysql_database}'")
    if cursor.fetchone():
        print(f"   ✅ Database '{mysql_database}' exists")
    else:
        print(f"   ⚠️  Database '{mysql_database}' does not exist")
        print(f"   → Creating database...")
        cursor.execute(f"CREATE DATABASE {mysql_database}")
        print(f"   ✅ Database '{mysql_database}' created")
    
    cursor.close()
    connection.close()
    
except mysql.connector.Error as e:
    print(f"   ❌ MySQL connection failed: {e}")
    print("\n   Troubleshooting:")
    print("   → Make sure MySQL is running")
    print("   → Check credentials in .env file")
    print("   → For free MySQL: https://railway.app or https://db4free.net")
    print("   → See DEPLOYMENT.md for setup instructions")

# Check Redis configuration
print("\n5️⃣ Checking Redis Configuration...")
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', 6379)

print(f"   Host: {redis_host}")
print(f"   Port: {redis_port}")

# Try to connect to Redis
try:
    import redis
    print("\n   Testing Redis connection...")
    r = redis.Redis(host=redis_host, port=int(redis_port), db=0)
    r.ping()
    print("   ✅ Redis connection successful!")
    
except Exception as e:
    print(f"   ❌ Redis connection failed: {e}")
    print("\n   Troubleshooting:")
    print("   → Make sure Redis is running")
    print("   → Windows: Download from https://github.com/microsoftarchive/redis/releases")
    print("   → For free Redis: https://redis.com/try-free (30MB free)")
    print("   → See DEPLOYMENT.md for setup instructions")

# Check scraping dependencies
print("\n6️⃣ Checking Scraping Dependencies...")
try:
    import selenium
    print("   ✅ Selenium installed")
except ImportError:
    print("   ❌ Selenium not installed")

try:
    import undetected_chromedriver
    print("   ✅ Undetected ChromeDriver installed")
except ImportError:
    print("   ❌ Undetected ChromeDriver not installed")

try:
    from bs4 import BeautifulSoup
    print("   ✅ BeautifulSoup installed")
except ImportError:
    print("   ❌ BeautifulSoup not installed")

# Summary
print("\n" + "="*50)
print("📊 Configuration Summary")
print("="*50)

all_good = True

if not bot_token or bot_token == 'your_telegram_bot_token_here':
    print("❌ Bot token needs configuration")
    all_good = False

try:
    import mysql.connector
    connection = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    connection.close()
    print("✅ MySQL ready")
except:
    print("❌ MySQL needs setup")
    all_good = False

try:
    import redis
    r = redis.Redis(host=redis_host, port=int(redis_port), db=0)
    r.ping()
    print("✅ Redis ready")
except:
    print("⚠️  Redis not available (bot will still work but without caching)")

if all_good:
    print("\n🎉 All critical configurations are ready!")
    print("\n▶️  You can now run: python main.py")
else:
    print("\n⚠️  Please fix the issues above before running the bot")
    print("\n📖 Check DEPLOYMENT.md for detailed setup instructions")
    print("🆓 See free database options for MySQL and Redis")
