import mysql.connector
from mysql.connector import Error
import config
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(**config.MYSQL_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    connection = get_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                job_type VARCHAR(50),
                work_mode VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # User domains table (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_domains (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                domain VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_domain (user_id, domain)
            )
        """)
        
        # Jobs table
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
                UNIQUE KEY unique_job (title, company, source)
            )
        """)
        
        # Sent notifications table (to avoid duplicate sends)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sent_notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                job_id INT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                UNIQUE KEY unique_notification (user_id, job_id)
            )
        """)
        
        connection.commit()
        logger.info("Database initialized successfully")
        return True
        
    except Error as e:
        logger.error(f"Database initialization error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def save_user(user_id, username, first_name, job_type, work_mode, domains):
    """Save or update user preferences"""
    connection = get_connection()
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
        
        # Insert new domains
        for domain in domains:
            cursor.execute("""
                INSERT INTO user_domains (user_id, domain)
                VALUES (%s, %s)
            """, (user_id, domain))
        
        connection.commit()
        return True
        
    except Error as e:
        logger.error(f"Error saving user: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_user(user_id):
    """Get user preferences"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute("SELECT domain FROM user_domains WHERE user_id = %s", (user_id,))
            domains = [row['domain'] for row in cursor.fetchall()]
            user['domains'] = domains
        
        return user
        
    except Error as e:
        logger.error(f"Error getting user: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def save_jobs(jobs_list):
    """Save scraped jobs to database"""
    connection = get_connection()
    if not connection:
        return 0
    
    saved_count = 0
    try:
        cursor = connection.cursor()
        
        for job in jobs_list:
            try:
                cursor.execute("""
                    INSERT INTO jobs (title, company, location, job_type, work_mode, 
                                     domain, url, description, source, posted_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        location = VALUES(location),
                        description = VALUES(description),
                        scraped_at = CURRENT_TIMESTAMP
                """, (job['title'], job['company'], job['location'], job['job_type'],
                      job['work_mode'], job['domain'], job['url'], job['description'],
                      job['source'], job['posted_date']))
                saved_count += 1
            except Error:
                continue
        
        connection.commit()
        logger.info(f"Saved {saved_count} jobs to database")
        return saved_count
        
    except Error as e:
        logger.error(f"Error saving jobs: {e}")
        return 0
    finally:
        cursor.close()
        connection.close()

def get_matching_jobs(user_id, limit=4):
    """Get jobs matching user preferences that haven't been sent"""
    connection = get_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT j.* FROM jobs j
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
        cursor.close()
        connection.close()

def mark_notification_sent(user_id, job_id):
    """Mark a job notification as sent to user"""
    connection = get_connection()
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
        cursor.close()
        connection.close()

def get_all_active_users():
    """Get all active users"""
    connection = get_connection()
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
        cursor.close()
        connection.close()
