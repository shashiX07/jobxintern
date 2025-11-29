import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging
import random
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

def get_driver():
    """Create undetected Chrome driver"""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f'user-agent={UserAgent().random}')
    
    # Try to find Chrome binary on Linux
    import platform
    if platform.system() == 'Linux':
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/snap/bin/chromium'
        ]
        import os
        for path in chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                logger.info(f"Using Chrome binary at: {path}")
                break
    
    try:
        driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
        return driver
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        logger.info("Chrome/Chromium may not be installed. Install with: sudo apt install chromium-browser")
        return None

def scrape_linkedin_jobs(job_type, work_mode, domain, max_jobs=10):
    """Scrape jobs from LinkedIn"""
    jobs = []
    driver = None
    
    try:
        driver = get_driver()
        if not driver:
            return jobs
        
        # Build search URL
        keywords = domain.replace(' ', '%20')
        location = 'India'
        job_type_filter = 'I' if job_type == 'Internship' else 'F'
        
        url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_JT={job_type_filter}"
        
        try:
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # Scroll to load more jobs
            for _ in range(3):
                driver.execute_script('window.scrollBy(0, window.innerHeight)')
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
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip(),
                            'location': location_elem.text.strip() if location_elem else 'Remote',
                            'job_type': job_type,
                            'work_mode': work_mode,
                            'domain': domain,
                            'url': link_elem.get('href', ''),
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
    finally:
        if driver:
            driver.quit()
    
    logger.info(f"Scraped {len(jobs)} jobs from LinkedIn for {domain}")
    return jobs

def scrape_internshala_jobs(job_type, work_mode, domain, max_jobs=10):
    """Scrape jobs/internships from Internshala"""
    jobs = []
    driver = None
    
    try:
        driver = get_driver()
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
            time.sleep(random.uniform(3, 5))
            
            # Scroll to load content
            for _ in range(2):
                driver.execute_script('window.scrollBy(0, window.innerHeight)')
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
                            job_url = 'https://internshala.com' + link_elem['href']
                        
                        jobs.append({
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip(),
                            'location': location_elem.text.strip() if location_elem else 'India',
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
    finally:
        if driver:
            driver.quit()
    
    logger.info(f"Scraped {len(jobs)} jobs from Internshala for {domain}")
    return jobs

async def scrape_jobs_for_preferences(job_type, work_mode, domains):
    """Scrape jobs from all sources for given preferences"""
    import asyncio
    all_jobs = []
    
    for domain in domains:
        # Scrape from both sources (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        
        linkedin_jobs = await loop.run_in_executor(
            None, scrape_linkedin_jobs, job_type, work_mode, domain, 5
        )
        all_jobs.extend(linkedin_jobs)
        
        await asyncio.sleep(random.uniform(3, 5))  # Delay between sources
        
        internshala_jobs = await loop.run_in_executor(
            None, scrape_internshala_jobs, job_type, work_mode, domain, 5
        )
        all_jobs.extend(internshala_jobs)
        
        await asyncio.sleep(random.uniform(2, 4))  # Delay between domains
    
    logger.info(f"Total scraped: {len(all_jobs)} jobs")
    return all_jobs
