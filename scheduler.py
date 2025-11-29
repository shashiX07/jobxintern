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
        
        self.tasks = [scraping_task, notification_task]
        logger.info("Scheduler started successfully")
    
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
        """Scrape jobs for all unique preference combinations"""
        if self.is_scraping:
            logger.info("Scraping already in progress, skipping...")
            return
        
        self.is_scraping = True
        logger.info("Starting job scraping...")
        
        try:
            connection = database.get_connection()
            if not connection:
                logger.error("Failed to connect to database for scraping")
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
            connection.close()
            
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
        """Send job notifications to all active users"""
        logger.info("Starting notification send...")
        
        try:
            active_users = database.get_all_active_users()
            
            sent_count = 0
            
            for user_id in active_users:
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
                        message = format_job_message(job)
                        
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            reply_markup=keyboards.get_job_actions_keyboard(job['url']),
                            parse_mode='HTML'
                        )
                        
                        # Mark as sent
                        database.mark_notification_sent(user_id, job['id'])
                        sent_count += 1
                        
                        # Small delay between messages
                        await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error sending notification to {user_id}: {e}")
                    continue
            
            logger.info(f"Notifications sent: {sent_count} jobs to {len(active_users)} users")
            
        except Exception as e:
            logger.error(f"Error in send_notifications: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("Scheduler stopped")
