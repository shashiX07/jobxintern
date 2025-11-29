import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
import database
from bot import start, callback_handler, message_handler, help_command
from scheduler import JobScheduler
from admin_commands import (
    admin_panel, manual_scrape, manual_notify, bot_stats,
    list_users, broadcast_message, clear_old_jobs, add_test_job
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot"""
    
    # Initialize database
    logger.info("Initializing database...")
    if not database.init_database():
        logger.error("Failed to initialize database. Exiting...")
        return
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Add admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("scrape", manual_scrape))
    application.add_handler(CommandHandler("notify", manual_notify))
    application.add_handler(CommandHandler("stats", bot_stats))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("clearjobs", clear_old_jobs))
    application.add_handler(CommandHandler("testjob", add_test_job))
    
    # Initialize scheduler
    scheduler = JobScheduler(application)
    scheduler.start()
    
    # Store scheduler in bot_data for admin commands
    application.bot_data['scheduler'] = scheduler
    
    logger.info("Bot started successfully!")
    
    # Start bot
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received stop signal")
    finally:
        scheduler.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
