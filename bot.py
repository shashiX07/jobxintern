import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import config
import database
import keyboards
from cache import cache
import logging

logger = logging.getLogger(__name__)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is member of required channels"""
    user_id = update.effective_user.id
    
    if not config.REQUIRED_CHANNELS:
        return True
    
    for channel_id in config.REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except TelegramError:
            logger.error(f"Error checking membership for channel {channel_id}")
            return False
    
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - check channels and begin onboarding"""
    user = update.effective_user
    
    # Check channel membership
    is_member = await check_channel_membership(update, context)
    
    if not is_member:
        await update.message.reply_text(
            "🔒 To use this bot, please join our channels first:\n\n"
            "After joining, click the button below to verify.",
            reply_markup=keyboards.get_channels_keyboard(config.REQUIRED_CHANNELS)
        )
        return
    
    # Check if user exists
    user_data = database.get_user(user.id)
    
    if user_data:
        await update.message.reply_text(
            f"👋 Welcome back, {user.first_name}!\n\n"
            f"You're all set up. Use the menu below to explore jobs.",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
    else:
        # Start onboarding
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
                "✅ Great! You've joined the channels.\n\n"
                "Now let's set up your preferences.\n\n"
                "What are you looking for?",
                reply_markup=keyboards.get_job_type_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ You haven't joined all channels yet.\n\n"
                "Please join all channels and try again.",
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
                    f"🎉 Setup complete!\n\n"
                    f"📋 Your Preferences:\n"
                    f"• Type: {state['job_type']}\n"
                    f"• Mode: {state['work_mode']}\n"
                    f"• Domains: {', '.join(domains)}\n\n"
                    f"You'll receive job notifications twice daily at {', '.join(config.NOTIFICATION_TIMES)}.\n\n"
                    f"Use the menu to view jobs anytime!",
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
    
    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "🤖 Bot Help\n\n"
            "This bot helps you find jobs and internships based on your preferences.\n\n"
            "📌 Features:\n"
            "• Personalized job recommendations\n"
            "• Notifications twice daily\n"
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
            "Jobs are scraped every 12 hours. Check back later!"
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await message_handler(update, context)
