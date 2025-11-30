from telegram import Update
from telegram.ext import ContextTypes
import config
import database
from scheduler import JobScheduler
import logging

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    logger.info(f"Admin check: user_id={user_id}, ADMIN_ID={config.ADMIN_ID}, match={user_id == config.ADMIN_ID}")
    return user_id == config.ADMIN_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin control panel"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    await update.message.reply_text(
        "👑 <b>Admin Control Panel</b>\n\n"
        "🔧 <b>Available Commands:</b>\n\n"
        "/scrape - Start scraping jobs now\n"
        "/notify - Send notifications to all users now\n"
        "/stats - View bot statistics\n"
        "/users - List all users\n"
        "/broadcast - Send message to all users\n"
        "/clearjobs - Clear old jobs from database\n"
        "/testjob - Add test job for testing\n"
        "/help - Show this menu",
        parse_mode='HTML'
    )

async def manual_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger scraping"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    msg = await update.message.reply_text("🔄 Starting manual scraping...")
    
    try:
        # Get the scheduler from context
        scheduler = context.application.bot_data.get('scheduler')
        if not scheduler:
            await msg.edit_text("❌ Scheduler not found!")
            return
        
        # Trigger scraping
        await scheduler.scrape_all_jobs()
        
        await msg.edit_text(
            "✅ <b>Scraping completed!</b>\n\n"
            "Check logs for details.\n"
            "Use /stats to see job count.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Manual scraping error: {e}")
        await msg.edit_text(f"❌ Scraping failed: {str(e)}")

async def manual_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually send notifications to all users"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    msg = await update.message.reply_text("📬 Sending notifications to all users...")
    
    try:
        scheduler = context.application.bot_data.get('scheduler')
        if not scheduler:
            await msg.edit_text("❌ Scheduler not found!")
            return
        
        # Send notifications
        await scheduler.send_notifications()
        
        await msg.edit_text(
            "✅ <b>Notifications sent!</b>\n\n"
            "Check logs for delivery status.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Manual notification error: {e}")
        await msg.edit_text(f"❌ Notification failed: {str(e)}")

async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    try:
        with database.get_connection() as connection:
            if not connection:
                await update.message.reply_text("❌ Database connection failed!")
                return
            
            cursor = connection.cursor(dictionary=True)
            
            # Get user count
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
            active_users = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            # Get job count
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            total_jobs = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE scraped_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            recent_jobs = cursor.fetchone()['count']
            
            # Get notification count
            cursor.execute("SELECT COUNT(*) as count FROM sent_notifications")
            total_notifications = cursor.fetchone()['count']
            
            # Get jobs by source
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM jobs 
                GROUP BY source
            """)
            sources = cursor.fetchall()
            
            # Get top domains
            cursor.execute("""
                SELECT domain, COUNT(*) as count 
                FROM user_domains 
                GROUP BY domain 
                ORDER BY count DESC 
                LIMIT 5
            """)
            top_domains = cursor.fetchall()
            
            cursor.close()
        
        # Format message
        source_text = "\n".join([f"   • {s['source']}: {s['count']}" for s in sources]) if sources else "   None"
        domain_text = "\n".join([f"   • {d['domain']}: {d['count']} users" for d in top_domains]) if top_domains else "   None"
        
        stats_message = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"👥 <b>Users:</b>\n"
            f"   • Active: {active_users}\n"
            f"   • Total: {total_users}\n\n"
            f"💼 <b>Jobs:</b>\n"
            f"   • Total: {total_jobs}\n"
            f"   • Last 24h: {recent_jobs}\n\n"
            f"📨 <b>Notifications:</b>\n"
            f"   • Total Sent: {total_notifications}\n\n"
            f"🔗 <b>Job Sources:</b>\n{source_text}\n\n"
            f"🎯 <b>Popular Domains:</b>\n{domain_text}"
        )
        
        await update.message.reply_text(stats_message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text(f"❌ Error getting stats: {str(e)}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    try:
        with database.get_connection() as connection:
            if not connection:
                await update.message.reply_text("❌ Database connection failed!")
                return
            
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT u.user_id, u.username, u.first_name, u.job_type, 
                       u.work_mode, u.is_active, u.created_at,
                       GROUP_CONCAT(ud.domain) as domains
                FROM users u
                LEFT JOIN user_domains ud ON u.user_id = ud.user_id
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
                LIMIT 20
            """)
            
            users = cursor.fetchall()
            cursor.close()
        
        if not users:
            await update.message.reply_text("📭 No users registered yet.")
            return
        
        user_list = ["👥 <b>Registered Users:</b>\n"]
        
        for user in users:
            status = "✅" if user['is_active'] else "❌"
            username = f"@{user['username']}" if user['username'] else "No username"
            domains = user['domains'].split(',') if user['domains'] else []
            domain_str = ", ".join(domains[:2]) if domains else "None"
            if len(domains) > 2:
                domain_str += "..."
            
            user_list.append(
                f"\n{status} <b>{user['first_name']}</b> ({username})\n"
                f"   ID: {user['user_id']}\n"
                f"   Type: {user['job_type']} | Mode: {user['work_mode']}\n"
                f"   Domains: {domain_str}\n"
                f"   Joined: {user['created_at']}"
            )
        
        message = "\n".join(user_list)
        
        if len(message) > 4000:
            message = message[:4000] + "\n\n... (truncated)"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        await update.message.reply_text(f"❌ Error listing users: {str(e)}")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    # Check if message provided
    if not context.args:
        await update.message.reply_text(
            "📢 <b>Broadcast Message</b>\n\n"
            "Usage: /broadcast <message>\n\n"
            "Example:\n"
            "/broadcast Hello everyone! New jobs available.",
            parse_mode='HTML'
        )
        return
    
    message = " ".join(context.args)
    
    try:
        active_users = database.get_all_active_users()
        
        if not active_users:
            await update.message.reply_text("📭 No active users to broadcast to.")
            return
        
        status_msg = await update.message.reply_text(
            f"📤 Broadcasting to {len(active_users)} users..."
        )
        
        success = 0
        failed = 0
        
        for user_id in active_users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 <b>Admin Message:</b>\n\n{message}",
                    parse_mode='HTML'
                )
                success += 1
            except Exception as e:
                logger.error(f"Broadcast failed for user {user_id}: {e}")
                failed += 1
        
        await status_msg.edit_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"✅ Sent: {success}\n"
            f"❌ Failed: {failed}",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await update.message.reply_text(f"❌ Broadcast failed: {str(e)}")

async def clear_old_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear jobs older than 7 days"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    try:
        with database.get_connection() as connection:
            if not connection:
                await update.message.reply_text("❌ Database connection failed!")
                return
            
            cursor = connection.cursor()
            
            # Delete old jobs
            cursor.execute("""
                DELETE FROM jobs 
                WHERE scraped_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            
            deleted = cursor.rowcount
            connection.commit()
            
            cursor.close()
        
        await update.message.reply_text(
            f"🗑️ <b>Cleanup Complete!</b>\n\n"
            f"Deleted {deleted} jobs older than 7 days.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Clear jobs error: {e}")
        await update.message.reply_text(f"❌ Cleanup failed: {str(e)}")

async def add_test_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a test job for testing notifications"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access required!")
        return
    
    try:
        test_jobs = [
            {
                'title': 'Test Python Developer Position',
                'company': 'Test Company Inc',
                'location': 'Remote',
                'job_type': 'Job',
                'work_mode': 'Remote',
                'domain': 'Python Developer',
                'url': 'https://example.com/test-job',
                'description': 'This is a test job for testing bot notifications',
                'source': 'TestSource',
                'posted_date': 'Today'
            },
            {
                'title': 'Test Web Development Internship',
                'company': 'Test Startup',
                'location': 'India',
                'job_type': 'Internship',
                'work_mode': 'Hybrid',
                'domain': 'Web Development',
                'url': 'https://example.com/test-internship',
                'description': 'Test internship for web developers',
                'source': 'TestSource',
                'posted_date': 'Today'
            }
        ]
        
        saved = database.save_jobs(test_jobs)
        
        await update.message.reply_text(
            f"✅ <b>Test Jobs Added!</b>\n\n"
            f"Added {saved} test jobs.\n\n"
            f"Use /notify to send them to users.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Add test job error: {e}")
        await update.message.reply_text(f"❌ Failed to add test jobs: {str(e)}")
