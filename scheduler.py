from datetime import datetime, time as dt_time
import asyncio
import logging
import database
from scraper import scrape_jobs_for_preferences
from bot import format_job_message
import keyboards
import config

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self, bot_application):
        self.bot = bot_application.bot
        self.is_scraping = False
        self.running = True
        self.tasks = []
    
    def start(self):
        """Start the scheduler tasks"""
        # Create background tasks
        scraping_task = asyncio.create_task(self._scraping_loop())
        notification_task = asyncio.create_task(self._notification_loop())
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.tasks = [scraping_task, notification_task, cleanup_task]
        logger.info("Scheduler started successfully with all optimization tasks")
    
    async def _scraping_loop(self):
        """Background loop for periodic scraping"""
        # Run immediately on start
        await self.scrape_all_jobs()
        
        # Then run every SCRAPE_INTERVAL_HOURS
        while self.running:
            await asyncio.sleep(config.SCRAPE_INTERVAL_HOURS * 3600)
            await self.scrape_all_jobs()
    
    async def _notification_loop(self):
        """Background loop for scheduled notifications"""
        while self.running:
            now = datetime.now()
            
            # Check if current time matches any notification time
            for time_str in config.NOTIFICATION_TIMES:
                hour, minute = map(int, time_str.split(':'))
                notification_time = dt_time(hour, minute)
                current_time = now.time()
                
                # Check if we're within 1 minute of notification time
                if (current_time.hour == notification_time.hour and 
                    current_time.minute == notification_time.minute):
                    await self.send_notifications()
                    # Sleep for 2 minutes to avoid duplicate sends
                    await asyncio.sleep(120)
                    break
            
            # Check every 30 seconds
            await asyncio.sleep(30)
    
    async def scrape_all_jobs(self):
        """Scrape jobs for all unique preference combinations with resource management"""
        if self.is_scraping:
            logger.info("Scraping already in progress, skipping...")
            return
        
        self.is_scraping = True
        logger.info("Starting job scraping...")
        
        try:
            with database.get_connection() as connection:
                if not connection:
                    logger.error("Failed to connect to database for scraping")
                    self.is_scraping = False
                    return
                
                cursor = connection.cursor(dictionary=True)
                
                # Get all unique preference combinations
                cursor.execute("""
                    SELECT DISTINCT u.job_type, u.work_mode, GROUP_CONCAT(ud.domain) as domains
                    FROM users u
                    INNER JOIN user_domains ud ON u.user_id = ud.user_id
                    WHERE u.is_active = TRUE
                    GROUP BY u.job_type, u.work_mode
                """)
                
                combinations = cursor.fetchall()
                cursor.close()
            
            if not combinations:
                logger.info("No active users found. Scraping skipped. Add users via /start on Telegram.")
                self.is_scraping = False
                return
            
            logger.info(f"Found {len(combinations)} preference combinations to scrape")
            total_scraped = 0
            
            for combo in combinations:
                domains = combo['domains'].split(',')
                job_type = combo['job_type']
                work_mode = combo['work_mode']
                
                logger.info(f"Scraping for: {job_type}, {work_mode}, {domains}")
                
                try:
                    jobs = await scrape_jobs_for_preferences(job_type, work_mode, domains)
                    saved = database.save_jobs(jobs)
                    total_scraped += saved
                    
                    # Small delay between combinations
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error scraping for combo: {e}")
                    continue
            
            logger.info(f"Scraping completed. Total saved: {total_scraped} jobs")
            
        except Exception as e:
            logger.error(f"Error in scrape_all_jobs: {e}")
        finally:
            self.is_scraping = False
    
    async def send_notifications(self):
        """Send job notifications to all active users with batch optimization"""
        logger.info("Starting notification send...")
        
        try:
            active_users = database.get_all_active_users()
            
            if not active_users:
                logger.info("No active users for notifications")
                return
            
            sent_count = 0
            failed_count = 0
            batch_notifications = []  # For batch marking
            
            # Process in batches of 10 users to manage resources
            batch_size = 10
            for i in range(0, len(active_users), batch_size):
                batch = active_users[i:i + batch_size]
                
                for user_id in batch:
                    try:
                        # Get matching jobs
                        jobs = database.get_matching_jobs(user_id, limit=3)
                        
                        if not jobs:
                            continue
                        
                        # Send notification message
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=f"🔔 <b>New Job Alert!</b>\n\n"
                                 f"Found {len(jobs)} new opportunities for you:\n",
                            parse_mode='HTML'
                        )
                        
                        # Send each job
                        for job in jobs:
                            try:
                                message = format_job_message(job)
                                
                                await self.bot.send_message(
                                    chat_id=user_id,
                                    text=message,
                                    reply_markup=keyboards.get_job_actions_keyboard(job['url']),
                                    parse_mode='HTML',
                                    disable_web_page_preview=True
                                )
                                
                                # Add to batch for marking
                                batch_notifications.append((user_id, job['id']))
                                sent_count += 1
                                
                                # Small delay to avoid rate limits
                                await asyncio.sleep(0.3)
                                
                            except Exception as e:
                                logger.error(f"Error sending job {job['id']} to {user_id}: {e}")
                                failed_count += 1
                                continue
                        
                    except Exception as e:
                        logger.error(f"Error processing notifications for {user_id}: {e}")
                        failed_count += 1
                        continue
                
                # Batch mark notifications after each batch of users
                if batch_notifications:
                    database.mark_notifications_batch(batch_notifications)
                    batch_notifications = []
                
                # Delay between batches
                if i + batch_size < len(active_users):
                    await asyncio.sleep(2)
            
            logger.info(f"Notifications completed: {sent_count} jobs sent, {failed_count} failed, {len(active_users)} users processed")
            
        except Exception as e:
            logger.error(f"Error in send_notifications: {e}")
    
    async def _cleanup_loop(self):
        """Background loop for database cleanup (runs daily at 3 AM)"""
        while self.running:
            now = datetime.now()
            
            # Run cleanup at 3 AM
            if now.hour == 3 and now.minute == 0:
                logger.info("Starting automated database cleanup...")
                try:
                    deleted = database.cleanup_old_data(days=30)
                    logger.info(f"Cleanup completed: {deleted} records removed")
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
                
                # Sleep for 2 minutes to avoid re-running
                await asyncio.sleep(120)
            
            # Check every 5 minutes
            await asyncio.sleep(300)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("Scheduler stopped")
