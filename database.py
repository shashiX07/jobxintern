import mysql.connector
from mysql.connector import pooling, Error
import config
import logging
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Connection pool for efficient resource management
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="job_bot_pool",
        pool_size=5,  # Adjust based on concurrent users
        pool_reset_session=True,
        **config.MYSQL_CONFIG
    )
    logger.info("Database connection pool created successfully")
except Error as e:
    logger.error(f"Failed to create connection pool: {e}")
    connection_pool = None

@contextmanager
def get_connection():
    """Get database connection from pool with automatic cleanup"""
    connection = None
    try:
        if connection_pool:
            connection = connection_pool.get_connection()
        else:
            connection = mysql.connector.connect(**config.MYSQL_CONFIG)
        yield connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        yield None
    finally:
        if connection and connection.is_connected():
            connection.close()

def init_database():
    """Initialize database tables with optimized indexes"""
    with get_connection() as connection:
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Users table with indexes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    job_type VARCHAR(50),
                    work_mode VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_is_active (is_active),
                    INDEX idx_job_type (job_type),
                    INDEX idx_work_mode (work_mode)
                )
            """)
        
            # User domains table with indexes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_domains (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    domain VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_domain (user_id, domain),
                    INDEX idx_domain (domain),
                    INDEX idx_user_id (user_id)
                )
            """)
        
            # Jobs table with comprehensive indexes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(500),
                    company VARCHAR(255),
                    location VARCHAR(255),
                    job_type VARCHAR(50),
                    work_mode VARCHAR(50),
                    domain VARCHAR(255),
                    url VARCHAR(1000),
                    description TEXT,
                    source VARCHAR(50),
                    posted_date VARCHAR(100),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_job (title(255), company(255), source),
                    INDEX idx_scraped_at (scraped_at),
                    INDEX idx_job_type (job_type),
                    INDEX idx_work_mode (work_mode),
                    INDEX idx_domain (domain),
                    INDEX idx_composite (domain, job_type, work_mode, scraped_at)
                )
            """)
        
            # Sent notifications table with indexes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    job_id INT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_notification (user_id, job_id),
                    INDEX idx_sent_at (sent_at),
                    INDEX idx_user_id (user_id)
                )
            """)
            
            connection.commit()
            logger.info("Database initialized successfully with optimized indexes")
            return True
            
        except Error as e:
            logger.error(f"Database initialization error: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

def save_user(user_id, username, first_name, job_type, work_mode, domains):
    """Save or update user preferences with batch insert"""
    with get_connection() as connection:
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Insert or update user
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, job_type, work_mode)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    username = %s,
                    first_name = %s,
                    job_type = %s,
                    work_mode = %s,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, username, first_name, job_type, work_mode,
                  username, first_name, job_type, work_mode))
            
            # Delete old domains
            cursor.execute("DELETE FROM user_domains WHERE user_id = %s", (user_id,))
            
            # Batch insert new domains
            if domains:
                domain_values = [(user_id, domain) for domain in domains]
                cursor.executemany("""
                    INSERT INTO user_domains (user_id, domain)
                    VALUES (%s, %s)
                """, domain_values)
            
            connection.commit()
            return True
            
        except Error as e:
            logger.error(f"Error saving user: {e}")
            connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

def get_user(user_id):
    """Get user preferences with single query"""
    with get_connection() as connection:
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Optimized single query with JOIN
            cursor.execute("""
                SELECT u.*, GROUP_CONCAT(ud.domain) as domains
                FROM users u
                LEFT JOIN user_domains ud ON u.user_id = ud.user_id
                WHERE u.user_id = %s
                GROUP BY u.user_id
            """, (user_id,))
            
            user = cursor.fetchone()
            
            if user and user['domains']:
                user['domains'] = user['domains'].split(',')
            elif user:
                user['domains'] = []
            
            return user
            
        except Error as e:
            logger.error(f"Error getting user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

def save_jobs(jobs_list):
    """Save scraped jobs to database with batch insert"""
    if not jobs_list:
        return 0
        
    with get_connection() as connection:
        if not connection:
            return 0
        
        saved_count = 0
        try:
            cursor = connection.cursor()
            
            # Batch insert for better performance
            job_values = []
            for job in jobs_list:
                job_values.append((
                    job['title'], job['company'], job['location'], job['job_type'],
                    job['work_mode'], job['domain'], job['url'], job['description'],
                    job['source'], job['posted_date']
                ))
            
            cursor.executemany("""
                INSERT INTO jobs (title, company, location, job_type, work_mode, 
                                 domain, url, description, source, posted_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    location = VALUES(location),
                    description = VALUES(description),
                    scraped_at = CURRENT_TIMESTAMP
            """, job_values)
            
            saved_count = cursor.rowcount
            connection.commit()
            logger.info(f"Saved {saved_count} jobs to database")
            return saved_count
            
        except Error as e:
            logger.error(f"Error saving jobs: {e}")
            connection.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()

def get_matching_jobs(user_id, limit=4):
    """Get jobs matching user preferences that haven't been sent (optimized query)"""
    with get_connection() as connection:
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Optimized query with indexes
            cursor.execute("""
                SELECT DISTINCT j.* 
                FROM jobs j
                INNER JOIN user_domains ud ON j.domain = ud.domain
                INNER JOIN users u ON ud.user_id = u.user_id
                LEFT JOIN sent_notifications sn ON j.id = sn.job_id AND sn.user_id = u.user_id
                WHERE u.user_id = %s
                    AND j.job_type = u.job_type
                    AND (j.work_mode = u.work_mode OR u.work_mode = 'Hybrid' OR j.work_mode = 'Hybrid')
                    AND sn.id IS NULL
                    AND j.scraped_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                ORDER BY j.scraped_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            return cursor.fetchall()
            
        except Error as e:
            logger.error(f"Error getting matching jobs: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

def mark_notification_sent(user_id, job_id):
    """Mark a job notification as sent to user"""
    with get_connection() as connection:
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO sent_notifications (user_id, job_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE sent_at = CURRENT_TIMESTAMP
            """, (user_id, job_id))
            connection.commit()
            return True
            
        except Error as e:
            logger.error(f"Error marking notification: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

def mark_notifications_batch(notifications):
    """Mark multiple notifications as sent in batch"""
    if not notifications:
        return 0
        
    with get_connection() as connection:
        if not connection:
            return 0
        
        try:
            cursor = connection.cursor()
            cursor.executemany("""
                INSERT INTO sent_notifications (user_id, job_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE sent_at = CURRENT_TIMESTAMP
            """, notifications)
            connection.commit()
            return cursor.rowcount
            
        except Error as e:
            logger.error(f"Error marking batch notifications: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()

def get_all_active_users():
    """Get all active users"""
    with get_connection() as connection:
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT user_id FROM users WHERE is_active = TRUE")
            return [row['user_id'] for row in cursor.fetchall()]
            
        except Error as e:
            logger.error(f"Error getting active users: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

def cleanup_old_data(days=30):
    """Clean up old jobs and notifications to optimize database"""
    with get_connection() as connection:
        if not connection:
            return 0
        
        try:
            cursor = connection.cursor()
            
            # Delete old jobs
            cursor.execute("""
                DELETE FROM jobs 
                WHERE scraped_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            
            deleted_jobs = cursor.rowcount
            
            # Delete orphaned notifications (jobs that no longer exist)
            cursor.execute("""
                DELETE sn FROM sent_notifications sn
                LEFT JOIN jobs j ON sn.job_id = j.id
                WHERE j.id IS NULL
            """)
            
            deleted_notifs = cursor.rowcount
            
            connection.commit()
            logger.info(f"Cleanup: {deleted_jobs} jobs, {deleted_notifs} notifications deleted")
            return deleted_jobs + deleted_notifs
            
        except Error as e:
            logger.error(f"Error cleaning up data: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
