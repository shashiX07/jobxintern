import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging
import random
from fake_useragent import UserAgent
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def get_driver():
    """Create undetected Chrome driver with automatic cleanup"""
    driver = None
    options = uc.ChromeOptions()
    
    # Performance optimizations
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-images')  # Don't load images
    options.add_argument('--disable-plugins')
    options.add_argument('--blink-settings=imagesEnabled=false')  # Additional image blocking
    options.add_argument('--disable-javascript')  # Disable JS where not needed
    options.add_argument('--window-size=1280,720')  # Smaller window
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument(f'user-agent={UserAgent().random}')
    
    # Try to find Chrome binary on Linux
    import platform
    import os
    if platform.system() == 'Linux':
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/snap/bin/chromium'
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                logger.info(f"Using Chrome binary at: {path}")
                break
    
    try:
        driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)
        yield driver
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        logger.info("Chrome/Chromium may not be installed. Install with: sudo apt install chromium-browser")
        yield None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def scrape_linkedin_jobs(job_type, work_mode, domain, max_jobs=10):
    """Scrape jobs from LinkedIn with optimized resource usage"""
    jobs = []
    
    try:
        with get_driver() as driver:
            if not driver:
                return jobs
            
            # Build search URL
            keywords = domain.replace(' ', '%20')
            location = 'India'
            job_type_filter = 'I' if job_type == 'Internship' else 'F'
            
            url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_JT={job_type_filter}"
            
            try:
                driver.get(url)
                time.sleep(random.uniform(2, 3))  # Reduced wait time
                
                # Optimized single scroll
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(1)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                job_cards = soup.find_all('div', class_='base-card', limit=max_jobs)
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h3', class_='base-search-card__title')
                        company_elem = card.find('h4', class_='base-search-card__subtitle')
                        location_elem = card.find('span', class_='job-search-card__location')
                        link_elem = card.find('a', class_='base-card__full-link')
                        
                        if title_elem and company_elem and link_elem:
                            jobs.append({
                                'title': title_elem.text.strip()[:500],  # Limit length
                                'company': company_elem.text.strip()[:255],
                                'location': (location_elem.text.strip() if location_elem else 'Remote')[:255],
                                'job_type': job_type,
                                'work_mode': work_mode,
                                'domain': domain,
                                'url': link_elem.get('href', '')[:1000],
                                'description': '',
                                'source': 'LinkedIn',
                                'posted_date': 'Recently'
                            })
                    except Exception as e:
                        logger.error(f"Error parsing job card: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error loading LinkedIn page: {e}")
        
    except Exception as e:
        logger.error(f"LinkedIn scraping error: {e}")
    
    logger.info(f"Scraped {len(jobs)} jobs from LinkedIn for {domain}")
    return jobs

def scrape_internshala_jobs(job_type, work_mode, domain, max_jobs=10):
    """Scrape jobs/internships from Internshala with optimized resource usage"""
    jobs = []
    
    try:
        with get_driver() as driver:
            if not driver:
                return jobs
            
            # Build search URL
            keywords = domain.lower().replace(' ', '-')
            
            if job_type == 'Internship':
                url = f"https://internshala.com/internships/{keywords}-internships"
            else:
                url = f"https://internshala.com/jobs/{keywords}-jobs"
            
            try:
                driver.get(url)
                time.sleep(random.uniform(2, 3))  # Reduced wait time
                
                # Optimized single scroll
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(1)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Internshala uses different classes for listings
                job_cards = soup.find_all('div', class_='individual_internship', limit=max_jobs)
                if not job_cards:
                    job_cards = soup.find_all('div', class_='internship_meta', limit=max_jobs)
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h3') or card.find('h4', class_='heading_4_5')
                        company_elem = card.find('p', class_='company-name') or card.find('div', class_='company')
                        location_elem = card.find('span', class_='location_link') or card.find('a', class_='location_link')
                        link_elem = card.find('a', class_='view_detail_button') or card.find('a', href=True)
                        
                        if title_elem and company_elem:
                            job_url = ''
                            if link_elem and link_elem.get('href'):
                                job_url = ('https://internshala.com' + link_elem['href'])[:1000]
                            
                            jobs.append({
                                'title': title_elem.text.strip()[:500],
                                'company': company_elem.text.strip()[:255],
                                'location': (location_elem.text.strip() if location_elem else 'India')[:255],
                                'job_type': job_type,
                                'work_mode': work_mode,
                                'domain': domain,
                                'url': job_url,
                                'description': '',
                                'source': 'Internshala',
                                'posted_date': 'Recently'
                            })
                    except Exception as e:
                        logger.error(f"Error parsing Internshala card: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error loading Internshala page: {e}")
        
    except Exception as e:
        logger.error(f"Internshala scraping error: {e}")
    
    logger.info(f"Scraped {len(jobs)} jobs from Internshala for {domain}")
    return jobs

async def scrape_jobs_for_preferences(job_type, work_mode, domains):
    """Scrape jobs from all sources with rate limiting and error recovery"""
    import asyncio
    all_jobs = []
    max_retries = 2
    
    for domain in domains:
        # Scrape from both sources with retries
        loop = asyncio.get_event_loop()
        
        # LinkedIn with retry
        for attempt in range(max_retries):
            try:
                linkedin_jobs = await loop.run_in_executor(
                    None, scrape_linkedin_jobs, job_type, work_mode, domain, 5
                )
                all_jobs.extend(linkedin_jobs)
                break
            except Exception as e:
                logger.error(f"LinkedIn scrape attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        
        await asyncio.sleep(random.uniform(2, 3))  # Reduced delay between sources
        
        # Internshala with retry
        for attempt in range(max_retries):
            try:
                internshala_jobs = await loop.run_in_executor(
                    None, scrape_internshala_jobs, job_type, work_mode, domain, 5
                )
                all_jobs.extend(internshala_jobs)
                break
            except Exception as e:
                logger.error(f"Internshala scrape attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        
        await asyncio.sleep(random.uniform(1, 2))  # Reduced delay between domains
    
    logger.info(f"Total scraped: {len(all_jobs)} jobs for {len(domains)} domains")
    return all_jobs
