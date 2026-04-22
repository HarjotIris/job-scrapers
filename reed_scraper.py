
import re, time, unicodedata, requests, bs4, random, json, pandas as pd, os, argparse, urllib.parse
# Get the directory where the current script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change working directory to script directory
os.chdir(script_dir)

class ReedScraper:
    def __init__(self, output_filename = 'jobs_reed_scraper', format = ''):
        self.job_skills_jones = []
        self.job_title_jones = []
        self.job_company_jones = []
        self.job_location_jones = []
        self.job_title_short_jones = [] 
        self.job_url_jones = []
        self.job_description_jones = []
        self.output_filename = output_filename
        self.json_filename = ''
        self.format = format.lower()
        self.job_salary_jones = []
        self.health_insurance_jones = []
        self.degree_jones = []
        self.remote_work_jones = []
        self.job_schedule_jones = []
        self.salary_rate_jones = []

    def normalize(self, text):
        return re.sub(r'[^a-z0-9]', '', text.lower().strip())


    def clean_text(self, text):
        """Clean text of problematic characters and encoding issues"""
        if not text:
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove or replace problematic characters
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '-')  # Em dash
        text = text.replace('\u2018', "'")  # Left single quotation mark
        text = text.replace('\u2019', "'")  # Right single quotation mark
        text = text.replace('\u201c', '"')  # Left double quotation mark
        text = text.replace('\u201d', '"')  # Right double quotation mark
        text = text.replace('\u00e9', 'e')  # é
        text = text.replace('\u00f1', 'n')  # ñ
        
        # Remove non-printable characters except newlines and tabs
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        
        return text.strip()
    

    def _extract_job_details(self, header_jones):
        # Extract Title
        try:
            temp_title_jones = header_jones.select_one('h2 a')
            temp_title_text_jones = temp_title_jones.getText(strip=True) or 'N/A'
        except (IndexError, AttributeError):
            temp_title_text_jones = 'N/A'
        
        # Extract Company
        temp_company_text_jones = 'N/A'
        try:
            company_elem = header_jones.select_one('div[data-qa="job-posted-by"] a')
            if company_elem:
                temp_company_text_jones = company_elem.getText(strip=True) or 'N/A'
        except:
            pass
        
        # Extract Location - FIXED
        temp_location_text_jones = 'N/A'
        try:
            # Look for location in the metadata list
            location_elem = header_jones.select_one('li[data-qa="job-metadata-location"]')
            if location_elem:
                temp_location_text_jones = location_elem.getText(strip=True) or 'N/A'
        except:
            pass
        
        # Extract Salary - ADD THIS (from search results page)
        temp_salary_text_jones = 'N/A'
        try:
            salary_elem = header_jones.select_one('li[data-qa="job-metadata-salary"]')
            if salary_elem:
                temp_salary_text_jones = salary_elem.getText(strip=True) or 'N/A'
        except:
            pass
        
        # Extract URL
        temp_job_url = 'N/A'
        try:
            temp_url_jones = header_jones.select_one('h2 a')
            if temp_url_jones and temp_url_jones.get('href'):
                href = temp_url_jones.get('href')
                if href.startswith('/'):
                    temp_job_url = 'https://www.reed.co.uk' + href
                else:
                    temp_job_url = href
        except:
            pass
        
        return temp_title_text_jones, temp_company_text_jones, temp_location_text_jones, temp_job_url, temp_salary_text_jones
    
    def _categorize_job_title(self, job_title):
        """
        Categorize job title into standardized short titles
        Uses keyword matching with priority order (specific → general → catch-all)
        """
        title_lower = job_title.lower()
        
        # Define categories with their keywords (order matters - check specific first!)
        categories = [
            # ========== SENIOR POSITIONS (Most Specific First) ==========
            
            # Senior Machine Learning
            ('Senior Machine Learning Engineer', ['senior', 'machine learning', 'engineer']),
            ('Senior Machine Learning Engineer', ['senior', 'ml', 'engineer']),
            ('Senior Machine Learning Engineer', ['senior', 'machine learning', 'scientist']),
            ('Senior Machine Learning Engineer', ['senior', 'mlops']),
            
            # Senior Data Science
            ('Senior Data Scientist', ['senior', 'data scientist']),
            ('Senior Data Scientist', ['senior', 'data science']),
            ('Senior Data Scientist', ['senior', 'applied', 'scientist']),
            ('Senior Data Scientist', ['senior', 'research', 'data']),
            
            # Senior Data Engineering
            ('Senior Data Engineer', ['senior', 'data engineer']),
            ('Senior Data Engineer', ['senior', 'data engineering']),
            ('Senior Data Engineer', ['senior', 'analytics', 'engineer']),
            ('Senior Data Engineer', ['senior', 'etl', 'engineer']),
            ('Senior Data Engineer', ['senior', 'data platform', 'engineer']),
            ('Senior Data Engineer', ['senior', 'data pipeline', 'engineer']),
            
            # Senior Data Analyst - ALL VARIATIONS
            ('Senior Data Analyst', ['senior', 'data analyst']),
            ('Senior Data Analyst', ['senior', 'data quality', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data governance', 'analyst']),
            ('Senior Data Analyst', ['senior', 'category data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data strategy', 'analyst']),
            ('Senior Data Analyst', ['senior', 'analytics', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data insights', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data operations', 'analyst']),
            ('Senior Data Analyst', ['senior', 'marketing', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'financial', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'product', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'customer', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'sales', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'business', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data reporting', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data visualization', 'analyst']),
            
            # Senior Business Intelligence
            ('Senior Business Analyst', ['senior', 'business intelligence', 'analyst']),
            ('Senior Business Analyst', ['senior', 'bi analyst']),
            ('Senior Business Analyst', ['senior', 'business analyst']),
            ('Senior Business Analyst', ['senior', 'business systems', 'analyst']),
            
            # Senior Software Engineering
            ('Senior Software Engineer', ['senior', 'software', 'engineer']),
            ('Senior Software Engineer', ['senior', 'software', 'developer']),
            ('Senior Software Engineer', ['senior', 'backend', 'engineer']),
            ('Senior Software Engineer', ['senior', 'frontend', 'engineer']),
            ('Senior Software Engineer', ['senior', 'full stack']),
            ('Senior Software Engineer', ['senior', 'developer']),
            
            # ========== LEAD/PRINCIPAL/STAFF POSITIONS ==========
            
            ('Lead Data Scientist', ['lead', 'data scientist']),
            ('Lead Data Scientist', ['staff', 'data scientist']),
            ('Lead Data Engineer', ['lead', 'data engineer']),
            ('Lead Data Engineer', ['staff', 'data engineer']),
            ('Principal Data Scientist', ['principal', 'data scientist']),
            ('Principal Data Scientist', ['principal', 'scientist']),
            ('Lead Machine Learning Engineer', ['lead', 'machine learning']),
            ('Lead Machine Learning Engineer', ['lead', 'ml', 'engineer']),
            
            # ========== MACHINE LEARNING ROLES ==========
            
            ('Machine Learning Engineer', ['machine learning', 'engineer']),
            ('Machine Learning Engineer', ['ml', 'engineer']),
            ('Machine Learning Engineer', ['machine learning', 'scientist']),
            ('Machine Learning Engineer', ['mlops', 'engineer']),
            ('Machine Learning Engineer', ['deep learning', 'engineer']),
            ('AI Engineer', ['ai', 'engineer']),
            ('AI Engineer', ['artificial intelligence', 'engineer']),
            ('AI Engineer', ['ai/ml']),
            
            # ========== DATA SCIENCE ROLES ==========
            
            ('Data Scientist', ['data scientist']),
            ('Data Scientist', ['data science']),
            ('Data Scientist', ['applied', 'scientist']),
            ('Research Scientist', ['research', 'scientist']),
            ('Research Scientist', ['research', 'data']),
            
            # ========== DATA ENGINEERING ROLES ==========
            
            ('Data Engineer', ['data engineer']),
            ('Data Engineer', ['data engineering']),
            ('Data Engineer', ['etl', 'engineer']),
            ('Data Engineer', ['data platform', 'engineer']),
            ('Data Engineer', ['data pipeline', 'engineer']),
            ('Data Engineer', ['data warehouse', 'engineer']),
            ('Analytics Engineer', ['analytics', 'engineer']),
            ('Analytics Engineer', ['analytics engineering']),
            
            # ========== DATA ANALYSIS ROLES - ALL VARIATIONS ==========
            
            ('Data Analyst', ['data analyst']),
            ('Data Analyst', ['data quality', 'analyst']),
            ('Data Analyst', ['data governance', 'analyst']),
            ('Data Analyst', ['category data', 'analyst']),
            ('Data Analyst', ['data strategy', 'analyst']),
            ('Data Analyst', ['analytics', 'analyst']),
            ('Data Analyst', ['data insights', 'analyst']),
            ('Data Analyst', ['data operations', 'analyst']),
            ('Data Analyst', ['marketing', 'data', 'analyst']),
            ('Data Analyst', ['financial', 'data', 'analyst']),
            ('Data Analyst', ['product', 'data', 'analyst']),
            ('Data Analyst', ['customer', 'data', 'analyst']),
            ('Data Analyst', ['sales', 'data', 'analyst']),
            ('Data Analyst', ['business', 'data', 'analyst']),
            ('Data Analyst', ['data reporting', 'analyst']),
            ('Data Analyst', ['data visualization', 'analyst']),
            ('Data Analyst', ['data analytics']),
            
            # Business Intelligence
            ('Business Intelligence Analyst', ['business intelligence', 'analyst']),
            ('Business Intelligence Analyst', ['bi analyst']),
            ('Business Intelligence Analyst', ['business intelligence']),
            ('Business Intelligence Analyst', ['bi developer']),
            
            # ========== BUSINESS ANALYST ROLES ==========
            
            ('Business Analyst', ['business analyst']),
            ('Business Analyst', ['business systems', 'analyst']),
            ('Business Analyst', ['functional', 'analyst']),
            ('Business Analyst', ['process', 'analyst']),
            
            # ========== QUANTITATIVE ROLES ==========
            
            ('Quantitative Analyst', ['quantitative', 'analyst']),
            ('Quantitative Analyst', ['quant', 'analyst']),
            ('Quantitative Analyst', ['quantitative', 'researcher']),
            ('Quantitative Analyst', ['quant', 'developer']),
            
            # ========== SOFTWARE ENGINEERING ROLES ==========
            
            ('Software Engineer', ['software', 'engineer']),
            ('Software Engineer', ['software', 'developer']),
            ('Backend Engineer', ['backend', 'engineer']),
            ('Backend Engineer', ['back-end', 'engineer']),
            ('Frontend Engineer', ['frontend', 'engineer']),
            ('Frontend Engineer', ['front-end', 'engineer']),
            ('Full Stack Engineer', ['full stack']),
            ('Full Stack Engineer', ['fullstack']),
            ('DevOps Engineer', ['devops']),
            ('DevOps Engineer', ['dev ops']),
            ('DevOps Engineer', ['site reliability', 'engineer']),
            ('DevOps Engineer', ['sre']),
            
            # ========== CLOUD ROLES ==========
            
            ('Cloud Engineer', ['cloud', 'engineer']),
            ('Cloud Engineer', ['cloud', 'developer']),
            ('Cloud Architect', ['cloud', 'architect']),
            ('Cloud Architect', ['solutions', 'architect', 'cloud']),
            
            # ========== ARCHITECT ROLES ==========
            
            ('Data Architect', ['data', 'architect']),
            ('Solutions Architect', ['solutions', 'architect']),
            ('Enterprise Architect', ['enterprise', 'architect']),
            
            # ========== CATCH-ALL PATTERNS (Ordered by Priority) ==========
            # These catch anything we missed with specific patterns
            
            # Catch any Senior + Data + Analyst combination
            ('Senior Data Analyst', ['senior', 'data', 'analyst']),
            
            # Catch any Senior + Data + Engineer combination
            ('Senior Data Engineer', ['senior', 'data', 'engineer']),
            
            # Catch any Senior + Data + Scientist combination
            ('Senior Data Scientist', ['senior', 'data', 'scientist']),
            
            # Catch any Senior + ML/Machine Learning combination
            ('Senior Machine Learning Engineer', ['senior', 'machine', 'learning']),
            ('Senior Machine Learning Engineer', ['senior', 'ml']),
            
            # Catch any Senior + Software/Developer combination
            ('Senior Software Engineer', ['senior', 'software']),
            ('Senior Software Engineer', ['senior', 'engineer']),
            

            # ========== OTHER ANALYST TYPES (Add before final catch-all) ==========

            ('Financial Analyst', ['financial', 'analyst']),
            ('Financial Analyst', ['finance', 'analyst']),
            ('Risk Analyst', ['risk', 'analyst']),
            ('Operations Analyst', ['operations', 'analyst']),
            ('Junior Analyst', ['junior', 'analyst']),

            # Catch any Data + Analyst combination (non-senior)
            ('Data Analyst', ['data', 'analyst']),

            # Generic analyst (for anything that doesn't fit above)
            ('Analyst', ['analyst']),
            
            # Catch any Data + Engineer combination (non-senior)
            ('Data Engineer', ['data', 'engineer']),
            
            # Catch any Data + Scientist combination (non-senior)
            ('Data Scientist', ['data', 'scientist']),
            
            # Catch any ML/Machine Learning Engineer (non-senior)
            ('Machine Learning Engineer', ['machine', 'learning']),
            ('Machine Learning Engineer', ['ml']),
            
            # Catch any AI-related roles
            ('AI Engineer', ['ai']),
            ('AI Engineer', ['artificial', 'intelligence']),
            
            # Catch any Business Analyst variations
            ('Business Analyst', ['business', 'analyst']),
            
            # Catch any Software Engineer variations
            ('Software Engineer', ['software']),
            ('Software Engineer', ['developer']),
            ('Software Engineer', ['engineer']),
        ]
        
        # Check each category
        for category_name, keywords in categories:
            # Check if ALL keywords are in the title
            if all(keyword in title_lower for keyword in keywords):
                return category_name
        
        # If no match found, return "Other"
        return 'Other'
        

    def _extract_job_description(self, job_url):
        jd_res = requests.get(job_url)
        soup_jd = bs4.BeautifulSoup(jd_res.text, 'html.parser')

        # Extract salary if not already extracted
        temp_pay_text_jones = 'N/A'
        try:
            # Try to find salary using different selectors
            temp_pay_jones = soup_jd.select_one('li:contains("£")')
            if not temp_pay_jones:
                temp_pay_jones = soup_jd.select_one('li[data-qa="job-salary"]')
            if temp_pay_jones:
                temp_pay_text_jones = temp_pay_jones.getText(strip=True) or 'N/A'
        except Exception:
            temp_pay_text_jones = 'N/A'
        
        # Only update salary if it was N/A from search results
        if self.job_salary_jones and self.job_salary_jones[-1] == 'N/A':
            self.job_salary_jones[-1] = temp_pay_text_jones
        
        # Extract salary rate
        salary_rate = self._salary_rate(temp_pay_text_jones)
        print(f"DEBUG: salary_rate = '{salary_rate}'")  # ADD THIS
        self.salary_rate_jones.append(salary_rate)

                # Extract schedule
        temp_job_schedule_text_jones = 'N/A'
        try:
            # Look for schedule in the metadata list
            metadata_items = soup_jd.select('ul[data-qa="job-metadata"] li')
            for item in metadata_items:
                text = item.getText(strip=True)
                # Check if this item contains schedule keywords
                if any(word in text.lower() for word in ['permanent', 'contract', 'full-time', 'part-time', 'temporary', 'freelance']):
                    temp_job_schedule_text_jones = text
                    break
        except Exception:
            temp_job_schedule_text_jones = 'N/A'
        self.job_schedule_jones.append(temp_job_schedule_text_jones)

        # Extract description
        try:                        
            div_jd = soup_jd.select('[data-qa="job-description"]')
            full_job_description = []
            for element in div_jd[0]:
                jd = element.getText(separator=' ').encode('utf-8', errors='ignore').decode('utf-8').strip()
                jd = self.clean_text(jd)
                jd = re.sub(r'\?', '', jd)
                jd = re.sub(r'\s+', ' ', jd)
                jd = re.sub(r':', '-', jd)
                jd = re.sub(r'\.', '', jd)
                full_job_description.append(jd)

            filtered_jd = [s for s in full_job_description if s != '']
            filtered_jd = '. '.join(filtered_jd).strip()
            filtered_jd += '.'
            return filtered_jd
                    
        except Exception as e:
            return f'No job description, exception {e} occured'

    # dump it all in csv_jones
    def _save_to_csv(self):
        import csv
        with open(self.output_filename + '.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Company', 'Location', 'URL', 'Job Description', 'Skills'])
            for title,title_short, company, location, u, desc, skills, salary, health_insurance, degree, remote, schedule, salary_rate in zip(self.job_title_jones, self.job_title_short_jones, self.job_company_jones, self.job_location_jones, self.job_url_jones, self.job_description_jones, self.job_skills_jones, self.job_salary_jones, self.health_insurance_jones, self.degree_jones, self.remote_work_jones, self.job_schedule_jones, self.salary_rate_jones):
                print(f"Title : {title}")
                print(f"Title Short : {title_short}")
                print(f'Company : {company}')
                print(f'Location : {location}')
                print(f'Job URL : {u}')
                print(f'Job Salary : {salary}')
                print(f'Job Health Insurance : {health_insurance}')
                print(f'Degree : {degree}')
                print(f'Remote Work : {remote}')
                print(f'Job via Reed')
                print(f'Job Schedule: {schedule}')
                print(f'Salary Rate: {salary_rate}')
                        
                print('='*10)
                print('='*10)
                writer.writerow([title.strip(),
                title_short.strip(),
                company.strip(),
                location.strip(),
                u.strip(),
                desc.strip(),
                skills.strip(),
                salary.strip(),
                health_insurance.strip(),
                degree.strip(),
                remote.strip(),
                'Reed',
                schedule.strip(),
                salary_rate.strip(),
                'London'])
                
    def _extract_skills(self, job_description):
        """Extract common skills from job description"""
        skills_list = [
            'python', 'java', 'javascript', 'sql', 'c++', 'c#', 'php', 'ruby', 'swift',
            'excel', 'powerbi', 'tableau', 'power bi', 'looker', 'qlik',
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
            'machine learning', 'deep learning', 'data analysis', 'data analytics', 
            'statistical analysis', 'data visualization', 'data mining',
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
            'spark', 'hadoop', 'hive', 'kafka', 'airflow',
            'git', 'github', 'gitlab', 'jira', 'agile', 'scrum',
            'etl', 'data warehousing', 'data modeling', 'database',
            'mysql', 'postgresql', 'mongodb', 'oracle', 'sql server',
            'api', 'rest', 'json', 'xml', 'html', 'css',
            'communication', 'teamwork', 'problem solving', 'analytical'
        ]
        
        found_skills = []
        jd_lower = job_description.lower()
        
        for skill in skills_list:
            if skill in jd_lower:
                found_skills.append(skill)
        
        return ', '.join(found_skills) if found_skills else 'N/A'
    
    def _extract_degree(self, job_description):
        degree_list = ['bachelor\'s', 'master\'s', 'bachelors', 'masters']
        vague_list = ['relevant degree', 'degree']
        jd_lower = job_description.lower()
        
        for degree in degree_list:
            if degree in jd_lower:
                return degree
        for val in vague_list:
            if val in jd_lower:
                return 'degree mentioned vaguely'
        return 'No degree mentioned'
    
    def _extract_job_health_insurance_info(self, job_description):
        jd_lower = job_description.lower()
        
        return 'True' if 'health insurance' in jd_lower else 'False'
    def _extract_job_work_from_home(self, job_description):
        jd_lower = job_description.lower()
        
        return 'True' if 'remote' in jd_lower or 'hybrid' in jd_lower else 'False'
    
    def _salary_rate(self, salary):
        salary_lower = salary.lower()
        if 'annum' in salary_lower or 'year' in salary_lower or 'per year' in salary_lower or '/year' in salary_lower:
            return 'yearly'
        elif 'hour' in salary_lower or 'hourly' in salary_lower or 'per hour' in salary_lower or '/hour' in salary_lower:
            return 'hourly'
        elif 'competitive' in salary_lower or 'negotiable' in salary_lower:
            return 'competitive'
        else:
            return 'Not applicable'
        
    
    def _save_to_json(self):
        data = []
        self.json_filename = self.output_filename.replace('.csv', '.json')
        for title, title_short, company, location, u, desc, skills, salary, health_insurance, degree, remote, schedule, salary_rate in zip(self.job_title_jones, self.job_title_short_jones, self.job_company_jones, self.job_location_jones, self.job_url_jones, self.job_description_jones, self.job_skills_jones, self.job_salary_jones, self.health_insurance_jones, self.degree_jones, self.remote_work_jones, self.job_schedule_jones, self.salary_rate_jones):
            data.append({
            'title' : title.strip(),
            'title_short': title_short.strip(),
            'company' : company.strip(),
            'location' : location.strip(),
            'job_url' : u.strip(),
            'job_description': desc.strip(),
            'skills': skills.strip(),
            'salary': salary.strip(),
            'health_insurance': health_insurance.strip(),
            'degree': degree.strip(),
            'remote_work': remote,
            'job_via': 'Reed',
            'schedule': schedule.strip(),
            'salary_rate': salary_rate.strip(),
            'city': 'London'
        })

        with open(f'{self.json_filename}', 'w') as f:
            json.dump(data, f, indent=4)
    def _send_to_pipeline(self):
            webhook_url = os.environ.get("N8N_WEBHOOK_REED", "https://primary-production-dacdb.up.railway.app/webhook/reed")
            all_jobs=[]
            for item in zip(self.job_title_jones, self.job_company_jones, self.job_location_jones, self.job_url_jones, 
                            self.job_skills_jones, self.job_salary_jones, self.remote_work_jones, self.job_schedule_jones):
                title, company, loca, u, skills, salary, remote, schedule = item
                job = {
                    "job_title": title.strip(),
                    "company": company.strip(),
                    "location": loca.strip(),
                    "job_url": u.strip(),
                    "skills": skills.strip(),
                    "salary": salary.strip(),
                    "work_from_home": remote.strip(),
                    "schedule": schedule.strip(),
                    "job_via": "Reed",
                    "city": "London"
                }
                all_jobs.append(job)
            try:
                payload = {"jobs": all_jobs}
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                print(f"✓ Sent: {len(all_jobs)}")
            except requests.exceptions.RequestException as e:
                print(f"✗ Failed to send batch: {e}")
    def _save_to_excel(self):
        excel_filename = self.output_filename + '.xlsx'
        
        # Create new dataframe with scraped data
        new_df = pd.DataFrame({
            'Title': [title.strip() for title in self.job_title_jones],
            'Title_Short': [title_short.strip() for title_short in self.job_title_short_jones],
            'Company': [company.strip() for company in self.job_company_jones],
            'Location': [location.strip() for location in self.job_location_jones],
            'URL': [url.strip() for url in self.job_url_jones],
            'Job Description': [desc.strip() for desc in self.job_description_jones],
            'Skills': [skills.strip() for skills in self.job_skills_jones],
            'Salary' : [salary.strip() for salary in self.job_salary_jones],
            'Job_Health_Insurance': [hi.strip() for hi in self.health_insurance_jones],
            'Degree': [degree.strip() for degree in self.degree_jones],
            'Remote Work': [remote.strip() for remote in self.remote_work_jones],
            'Job_via': ['Reed' for i in range(len(self.job_title_jones))],
            'Job_Schedule': [schedule for schedule in self.job_schedule_jones],
            'Salary_rate': [salary_rate for salary_rate in self.salary_rate_jones],
            'City': 'London'
        })
        
        # Check if file exists
        if os.path.exists(excel_filename):
            # Read existing data
            existing_df = pd.read_excel(excel_filename, engine='openpyxl')
            # Append new data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Remove duplicates based on Title, Company, and Location
            combined_df = combined_df.drop_duplicates(subset=['Title', 'Company', 'Location'], keep='first')
            combined_df.to_excel(excel_filename, index=False, engine='openpyxl')
            
            print(f'Appended {len(new_df)} new jobs to {excel_filename}. Total jobs: {len(combined_df)}')
        else:
            # Create new file if it doesn't exist
            new_df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f'Created new file {excel_filename} with {len(new_df)} jobs')

    def clear_data(self):
        self.job_title_jones = []
        self.job_company_jones = []
        self.job_location_jones = []
        self.job_url_jones = []
        self.job_description_jones = []
        self.job_skills_jones = []
        self.job_salary_jones = []
        self.health_insurance_jones = []
        self.degree_jones = []
        self.remote_work_jones = []
        self.job_title_short_jones = [] 
        self.job_schedule_jones = []
        self.salary_rate_jones = []

    def scrape_jobs(self, job_keyword:str, n_pages = 10):
        job_keyword = re.sub(r'\s+','-',job_keyword.strip().lower())
        if n_pages == 0:
            print('Please enter a minimum value of 1')
            return
        seen_jobs = set()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        for i in range(1, n_pages+1):
            url = f'https://www.reed.co.uk/jobs/{job_keyword}-jobs-in-london?pageno={i}'
            
            try:
                res = requests.get(url=url, headers=headers)
                res.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f'Error loading url : {e}')
                return e
            
            soup = bs4.BeautifulSoup(res.text, "html.parser")
            job_cards = soup.select('article.card')
            
            print(f"Page {i}: Found {len(job_cards)} job cards")
            
            for job_card in job_cards:
                # Get the header section
                header_jones = job_card.select_one('header')
                if not header_jones:
                    continue
                    
                title, company, location, job_url, salary = self._extract_job_details(header_jones)
                if salary == "Training Course" or "Training Course" in title:
                    print(f"Skipping Training Course job: {title}")
                    continue
                
                # Skip if no title
                if title == 'N/A':
                    continue
                    
                # Create unique identifier
                job_identifier = f"{self.normalize(title)}_{self.normalize(company)}_{self.normalize(location)}"
                
                # Skip if duplicate
                if job_identifier in seen_jobs:
                    print(f"Skipping duplicate: {title} at {company} in {location}")
                    continue
                
                seen_jobs.add(job_identifier)
                
                # Append to all lists (MUST append to EVERY list)
                self.job_title_jones.append(title)
                self.job_title_short_jones.append(self._categorize_job_title(title))
                self.job_company_jones.append(company)
                self.job_location_jones.append(location)
                self.job_url_jones.append(job_url)
                self.job_salary_jones.append(salary)  # Added from search results
                
                if job_url != 'N/A':
                    try:
                        description = self._extract_job_description(job_url)
                        self.job_description_jones.append(description)
                        skills = self._extract_skills(description)
                        self.job_skills_jones.append(skills)
                        health_insurance = self._extract_job_health_insurance_info(description)
                        self.health_insurance_jones.append(health_insurance)
                        degree = self._extract_degree(description)
                        self.degree_jones.append(degree)
                        remote = self._extract_job_work_from_home(description)
                        self.remote_work_jones.append(remote)
                        # Note: schedule and salary_rate are already handled in _extract_job_description
                    except Exception as e:
                        print(f"Error extracting description for {title}: {e}")
                        self.job_description_jones.append('Error extracting description')
                        self.job_skills_jones.append('N/A')
                        self.health_insurance_jones.append('False')
                        self.degree_jones.append('No degree mentioned')
                        self.remote_work_jones.append('False')
                else:
                    self.job_description_jones.append('No job description available')
                    self.job_skills_jones.append('N/A')
                    self.health_insurance_jones.append('False')
                    self.degree_jones.append('No degree mentioned')
                    self.remote_work_jones.append('False')
                
                time.sleep(random.uniform(1, 2))
        
        # Print debug info
        print(f"\n=== SCRAPING COMPLETE ===")
        print(f"Total jobs found: {len(self.job_title_jones)}")
        print(f"Job descriptions: {len(self.job_description_jones)}")
        print(f"Salaries: {len(self.job_salary_jones)}")
        
        # Save based on format
        if self.format == 'csv':
            self._save_to_csv()
        elif self.format == 'json':
            self._save_to_json()
        elif self.format == 'excel':
            self._save_to_excel()
        elif self.format == 'pandas':
            self._save_to_csv()
            self._save_to_json()
        else:
            self._save_to_csv()
            self._save_to_json()
            self._save_to_excel()
            self._send_to_pipeline()
        
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scraper CLI')

    parser.add_argument('--filename', default='jobs', help='Name of the output file without any extensions')
    parser.add_argument('--job_keyword', nargs='+', required=True, help='Enter the job keyword you want to search within quotes')
    parser.add_argument('--number_of_pages', type=int, default=1, help='Enter the number of pages you want to scrape')
    parser.add_argument('--format', help='Enter the format you want the output in, either csv or json or pandas or all of them', default='all', choices=['csv', 'json', 'excel', 'pandas', 'all'])

    args = parser.parse_args()

    scraper = ReedScraper(output_filename=args.filename, format=args.format)
    job_keyword = ' '.join(args.job_keyword)
    result = scraper.scrape_jobs(job_keyword, args.number_of_pages)

    print(result)

'''
salary_year_avg:
=IF(
    OR(ISNUMBER(SEARCH("per hour", H2)), ISNUMBER(SEARCH("hourly", H2))),
    "",
    LET(
        s, SUBSTITUTE(H2, ",", ""),
        parts, TEXTSPLIT(s, {"-"," "}),
        nums, FILTER(--SUBSTITUTE(parts, "£", ""), ISNUMBER(--SUBSTITUTE(parts, "£", ""))),
        IFERROR(AVERAGE(nums), "")
    )
)


salary_hour_avg:
=IF(
    OR(ISNUMBER(SEARCH("per annum", H2)), ISNUMBER(SEARCH("yearly", H2))),
    "",
    LET(
        s, SUBSTITUTE(H2, ",", ""),
        parts, TEXTSPLIT(s, {"-"," "}),
        nums, FILTER(--SUBSTITUTE(parts, "£", ""), ISNUMBER(--SUBSTITUTE(parts, "£", ""))),
        IFERROR(AVERAGE(nums), "")
    )
)
'''