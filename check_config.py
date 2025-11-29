#!/usr/bin/env python3
"""
Quick diagnostic script to check configuration
"""
import os
import sys
from dotenv import load_dotenv

print("🔍 Checking Bot Configuration...")
print("=" * 50)

# Check if .env exists
if os.path.exists('.env'):
    print("✅ .env file found")
else:
    print("❌ .env file NOT found!")
    print("   Create .env file with BOT_TOKEN and ADMIN_ID")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Check BOT_TOKEN
bot_token = os.getenv('BOT_TOKEN')
if bot_token:
    print(f"✅ BOT_TOKEN: {bot_token[:20]}...{bot_token[-10:]}")
else:
    print("❌ BOT_TOKEN not set!")

# Check ADMIN_ID
admin_id = os.getenv('ADMIN_ID')
if admin_id:
    print(f"✅ ADMIN_ID: {admin_id}")
    try:
        admin_id_int = int(admin_id)
        print(f"   Parsed as integer: {admin_id_int}")
    except ValueError:
        print(f"❌ ADMIN_ID is not a valid integer!")
else:
    print("❌ ADMIN_ID not set!")

# Check MySQL
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_user = os.getenv('MYSQL_USER', 'root')
mysql_pass = os.getenv('MYSQL_PASSWORD', '')
mysql_db = os.getenv('MYSQL_DATABASE', 'job_bot')

print(f"\n📊 Database Config:")
print(f"   Host: {mysql_host}")
print(f"   User: {mysql_user}")
print(f"   Password: {'Set' if mysql_pass else 'Empty'}")
print(f"   Database: {mysql_db}")

# Check Redis
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', 6379)

print(f"\n🔴 Redis Config:")
print(f"   Host: {redis_host}")
print(f"   Port: {redis_port}")

print("\n" + "=" * 50)
print("✅ Configuration check complete!")
print("\nTo test with your Telegram user ID:")
print("   1. Message the bot")
print("   2. Check the logs for your user_id")
print("   3. Update ADMIN_ID in .env to match your user_id")
