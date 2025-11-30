import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import config
import database
import keyboards
from cache import cache
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is member of required channels"""
    user_id = update.effective_user.id
    
    if not config.REQUIRED_CHANNELS:
        logger.warning("No REQUIRED_CHANNELS configured - allowing access")
        return True
    
    for channel_id in config.REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            logger.info(f"User {user_id} status in channel {channel_id}: {member.status}")
            
            # Check if user is a member (including all valid statuses)
            if member.status in ['left', 'kicked']:
                logger.info(f"User {user_id} not in channel {channel_id} - status: {member.status}")
                return False
                
        except TelegramError as e:
            logger.error(f"Error checking membership for channel {channel_id}: {e}")
            logger.error(f"Make sure the bot is added as ADMIN in channel {channel_id}")
            # Return False only if it's a permission error
            if "not enough rights" in str(e).lower() or "chat not found" in str(e).lower():
                logger.error(f"Bot doesn't have admin rights in channel {channel_id}!")
            return False
    
    logger.info(f"User {user_id} verified in all channels")
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - check channels and begin onboarding"""
    user = update.effective_user
    
    # Check if user exists first
    user_data = database.get_user(user.id)
    
    if user_data:
        # Existing user - welcome back
        await update.message.reply_text(
            f"👋 Welcome back, {user.first_name}!\n\n"
            f"You're all set up. Use the menu below to explore jobs.",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return
    
    # New user - MUST check channel membership first
    if config.REQUIRED_CHANNELS:
        is_member = await check_channel_membership(update, context)
        
        if not is_member:
            await update.message.reply_text(
                "🔒 <b>Welcome to Job Alert Bot!</b>\n\n"
                "To use this bot, please join our required channel(s) first:\n\n"
                "After joining, click the '✅ I've Joined' button below to verify and continue.",
                parse_mode='HTML',
                reply_markup=keyboards.get_channels_keyboard(config.REQUIRED_CHANNELS)
            )
            return
    
    # Channel verified - Start onboarding for new user
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        f"Let's get you set up to receive personalized job notifications.\n\n"
        f"First, what are you looking for?",
        reply_markup=keyboards.get_job_type_keyboard()
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # Check membership callback
    if data == "check_membership":
        is_member = await check_channel_membership(update, context)
        if is_member:
            await query.edit_message_text(
                "✅ <b>Perfect! You've joined all required channels.</b>\n\n"
                "Now let's set up your job preferences.\n\n"
                "What are you looking for?",
                parse_mode='HTML',
                reply_markup=keyboards.get_job_type_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ <b>Channel Verification Failed</b>\n\n"
                "Please make sure you:\n"
                "1. Clicked on each channel link above\n"
                "2. Joined the channel(s)\n"
                "3. Then click '✅ I've Joined' button again\n\n"
                "<i>Note: You must join ALL channels to continue.</i>",
                parse_mode='HTML',
                reply_markup=keyboards.get_channels_keyboard(config.REQUIRED_CHANNELS)
            )
        return
    
    # Job type selection
    if data.startswith("jtype_"):
        job_type = data.split("_")[1]
        state = cache.get_user_state(user_id) or {}
        state['job_type'] = job_type
        cache.set_user_state(user_id, state)
        
        await query.edit_message_text(
            f"✅ Looking for: {job_type}\n\n"
            f"What's your preferred work mode?",
            reply_markup=keyboards.get_work_mode_keyboard()
        )
        return
    
    # Work mode selection
    if data.startswith("wmode_"):
        work_mode = data.split("_")[1]
        state = cache.get_user_state(user_id) or {}
        state['work_mode'] = work_mode
        cache.set_user_state(user_id, state)
        
        await query.edit_message_text(
            f"✅ Work Mode: {work_mode}\n\n"
            f"Now select up to 3 domains you're interested in:\n"
            f"(Click on domains to select/deselect)",
            reply_markup=keyboards.get_domains_keyboard()
        )
        return
    
    # Domain selection
    if data.startswith("domain_"):
        if data == "domain_done":
            state = cache.get_user_state(user_id) or {}
            domains = state.get('domains', [])
            
            if not domains:
                await query.answer("Please select at least 1 domain!", show_alert=True)
                return
            
            # Save to database
            user = update.effective_user
            success = database.save_user(
                user.id, user.username, user.first_name,
                state['job_type'], state['work_mode'], domains
            )
            
            if success:
                cache.clear_user_state(user_id)
                await query.edit_message_text(
                    f"🎉 <b>Setup Complete!</b>\n\n"
                    f"📋 <b>Your Preferences:</b>\n"
                    f"• Type: {state['job_type']}\n"
                    f"• Mode: {state['work_mode']}\n"
                    f"• Domains: {', '.join(domains)}\n\n"
                    f"You'll receive job notifications <b>4 times daily</b> at {', '.join(config.NOTIFICATION_TIMES)}.\n\n"
                    f"Jobs are updated every <b>6 hours</b>. Use the menu to view jobs anytime!",
                    parse_mode='HTML',
                    reply_markup=None
                )
                
                # Send main menu
                await context.bot.send_message(
                    chat_id=user_id,
                    text="📱 Main Menu",
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
            else:
                await query.edit_message_text("❌ Error saving preferences. Please try again with /start")
        else:
            domain = data.replace("domain_", "")
            state = cache.get_user_state(user_id) or {}
            domains = state.get('domains', [])
            
            if domain in domains:
                domains.remove(domain)
            else:
                if len(domains) >= 3:
                    await query.answer("You can select maximum 3 domains!", show_alert=True)
                    return
                domains.append(domain)
            
            state['domains'] = domains
            cache.set_user_state(user_id, state)
            
            await query.edit_message_reply_markup(
                reply_markup=keyboards.get_domains_keyboard(domains)
            )
        return
    
    # Job navigation
    if data == "next_job":
        await show_jobs_to_user(update, context, is_callback=True)
        return
    
    if data == "close_job":
        await query.edit_message_text("Job listing closed. Use 🔍 View Jobs to see more opportunities!")
        return
    
    # Account management
    if data == "show_prefs":
        user_data = database.get_user(user_id)
        if user_data:
            await query.edit_message_text(
                f"📊 Your Preferences:\n\n"
                f"• Looking for: {user_data['job_type']}\n"
                f"• Work Mode: {user_data['work_mode']}\n"
                f"• Domains: {', '.join(user_data['domains'])}\n\n"
                f"Updated: {user_data['updated_at']}",
                reply_markup=keyboards.get_account_keyboard()
            )
        return
    
    if data == "update_prefs":
        await query.edit_message_text(
            "Let's update your preferences.\n\n"
            "What are you looking for?",
            reply_markup=keyboards.get_job_type_keyboard()
        )
        return
    
    if data == "back_menu":
        await query.message.reply_text(
            "📱 Main Menu",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        await query.message.delete()
        return

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from keyboard"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🔍 View Jobs":
        await show_jobs_to_user(update, context)
    
    elif text == "👤 My Account":
        user_data = database.get_user(user_id)
        if user_data:
            await update.message.reply_text(
                f"👤 Account Information\n\n"
                f"Name: {user_data['first_name']}\n"
                f"Username: @{user_data['username']}\n"
                f"Status: {'Active' if user_data['is_active'] else 'Inactive'}\n"
                f"Member since: {user_data['created_at']}",
                reply_markup=keyboards.get_account_keyboard()
            )
        else:
            await update.message.reply_text("Please complete setup first using /start")
    
    elif text == "⚙️ Change Preferences":
        await update.message.reply_text(
            "Let's update your preferences.\n\n"
            "What are you looking for?",
            reply_markup=keyboards.get_job_type_keyboard()
        )
    
    elif text == "📊 My Stats":
        await show_user_stats(update, context)
    
    elif text == "💡 Share Bot":
        await share_bot(update, context)
    
    elif text == "☕ Support Us":
        await show_donation(update, context)
    
    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "🤖 Bot Help\n\n"
            "This bot helps you find jobs and internships based on your preferences.\n\n"
            "📌 Features:\n"
            "• Personalized job recommendations\n"
            "• Notifications 4 times daily\n"
            "• Jobs updated every 6 hours\n"
            "• Jobs from LinkedIn & Internshala\n"
            "• Easy preference management\n\n"
            "🔧 Commands:\n"
            "/start - Setup or restart bot\n"
            "/help - Show this message\n\n"
            f"📬 Notifications: {', '.join(config.NOTIFICATION_TIMES)}",
            reply_markup=keyboards.get_main_menu_keyboard()
        )

async def show_jobs_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    """Show matching jobs to user"""
    user_id = update.effective_user.id
    
    # Get user preferences
    user_data = database.get_user(user_id)
    if not user_data:
        message = "Please complete setup first using /start"
        if is_callback:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Get matching jobs
    jobs = database.get_matching_jobs(user_id, limit=4)
    
    if not jobs:
        message = (
            "🔍 No new jobs found matching your preferences right now.\n\n"
            "Jobs are updated every 6 hours. Check back later!\n\n"
            "💡 Tip: Try sharing this bot with friends to help them find opportunities too!"
        )
        if is_callback:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Send first job
    job = jobs[0]
    message = format_job_message(job)
    
    if is_callback:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboards.get_job_actions_keyboard(job['url']),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=keyboards.get_job_actions_keyboard(job['url']),
            parse_mode='HTML'
        )
    
    # Mark as sent
    database.mark_notification_sent(user_id, job['id'])

def format_job_message(job):
    """Format job details for message"""
    return (
        f"<b>💼 {job['title']}</b>\n\n"
        f"🏢 Company: {job['company']}\n"
        f"📍 Location: {job['location']}\n"
        f"📋 Type: {job['job_type']}\n"
        f"💻 Mode: {job['work_mode']}\n"
        f"🎯 Domain: {job['domain']}\n"
        f"📅 Posted: {job['posted_date']}\n"
        f"🔗 Source: {job['source']}\n\n"
        f"{job['description'][:200] if job['description'] else 'Click View Details to learn more!'}"
    )

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's personal statistics"""
    user_id = update.effective_user.id
    
    try:
        connection = database.get_connection()
        if not connection:
            await update.message.reply_text("❌ Database error!")
            return
        
        cursor = connection.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            await update.message.reply_text("Please complete setup first using /start")
            cursor.close()
            connection.close()
            return
        
        # Get domains
        cursor.execute("SELECT domain FROM user_domains WHERE user_id = %s", (user_id,))
        domains = [d['domain'] for d in cursor.fetchall()]
        
        # Get notification count
        cursor.execute(
            "SELECT COUNT(*) as count FROM sent_notifications WHERE user_id = %s",
            (user_id,)
        )
        notif_count = cursor.fetchone()['count']
        
        cursor.close()
        connection.close()
        
        days_active = (datetime.now() - user['created_at']).days
        
        stats_text = (
            f"📊 <b>Your Statistics</b>\n\n"
            f"👤 <b>Name:</b> {user['first_name']}\n"
            f"🆔 <b>User ID:</b> {user_id}\n"
            f"📅 <b>Member Since:</b> {user['created_at'].strftime('%d %b %Y')}\n"
            f"⏰ <b>Active Days:</b> {days_active}\n\n"
            f"🎯 <b>Your Preferences:</b>\n"
            f"   • Type: {user['job_type']}\n"
            f"   • Mode: {user['work_mode']}\n"
            f"   • Domains: {', '.join(domains)}\n\n"
            f"📬 <b>Notifications Received:</b> {notif_count}\n"
            f"🔄 <b>Jobs Refresh:</b> Every 6 hours\n"
            f"📨 <b>Notification Times:</b> {', '.join(config.NOTIFICATION_TIMES)}\n\n"
            f"Keep checking for new opportunities! 🚀"
        )
        
        await update.message.reply_text(
            text=stats_text,
            parse_mode='HTML',
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await update.message.reply_text("❌ Error loading statistics")

async def share_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show share bot message"""
    bot_username = context.bot.username
    share_text = (
        "📢 <b>Share This Bot</b>\n\n"
        "Help your friends find job opportunities!\n\n"
        f"🔗 <b>Bot Link:</b> https://t.me/{bot_username}\n\n"
        "📱 <b>Share Message:</b>\n"
        f"<code>Check out this amazing job bot! It sends personalized job notifications 4 times daily 🚀\n\n"
        f"https://t.me/{bot_username}</code>\n\n"
        "<i>Tap to copy and share on WhatsApp, Telegram, or anywhere!</i> 💚"
    )
    
    await update.message.reply_text(
        text=share_text,
        parse_mode='HTML',
        reply_markup=keyboards.get_main_menu_keyboard()
    )

async def show_donation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show donation information"""
    donation_text = (
        "☕ <b>Support Our Bot</b>\n\n"
        f"{config.DONATION_MESSAGE}\n\n"
    )
    
    if config.DONATION_UPI:
        donation_text += (
            f"💳 <b>UPI ID:</b> <code>{config.DONATION_UPI}</code>\n"
            f"<i>(Tap to copy)</i>\n\n"
        )
    
    donation_text += (
        "🙏 <b>Your support helps us:</b>\n"
        "  • Keep servers running 24/7\n"
        "  • Add more job sources\n"
        "  • Improve features & speed\n"
        "  • Send faster notifications\n\n"
        "Thank you for considering! ❤️\n\n"
        "<i>Every contribution matters, no matter how small!</i>"
    )
    
    await update.message.reply_text(
        text=donation_text,
        parse_mode='HTML',
        reply_markup=keyboards.get_main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await message_handler(update, context)
