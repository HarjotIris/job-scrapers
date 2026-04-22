from selenium import webdriver
import re, unicodedata, json, pandas as pd, os
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import numpy as np
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
import argparse
import requests
from selenium.webdriver.common.keys import Keys
options = Options()
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
class AdzunaScraper:
    def __init__(self, output_filename = 'adzuna_jobs', format = 'all'):
        self.titles = []
        self.companies = []
        self.urls = []
        self.job_description= []
        self.job_skills = []
        self.output_filename = output_filename
        #self.json_filename = ''
        self.format = format.lower()
        self.job_title_short = []
        self.locations = []
        self.salary = []
        self.degree = []
        self.health_insurance = []
        self.work_from_home = []
        self.schedule = []
        self.salary_rate = []

    def normalize(self, text):
        return re.sub(r'[^a-z0-9]', '', text.lower().strip())
    
    def clean_text(self, text):
        """Clean text of problematic characters and encoding issues"""
        if not text:
            return ""
        
        text = unicodedata.normalize('NFKD', text)
        text = text.replace('\u00a0', ' ')
        text = text.replace('\u2013', '-')
        text = text.replace('\u2014', '-')
        text = text.replace('\u2018', "'")
        text = text.replace('\u2019', "'")
        text = text.replace('\u201c', '"')
        text = text.replace('\u201d', '"')
        text = text.replace('\u00e9', 'e')
        text = text.replace('\u00f1', 'n')
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        
        return text.strip()
    
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
            if 'annum' in salary or 'year' in salary:
                return 'yearly'
            elif 'hour' in salary or 'hourly' in salary:
                return 'hourly'
            elif 'day' in salary or 'daily' in salary:
                return 'daily'
            else:
                return 'Not applicable'
            
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
    
    def _shortening_titles(self):
        for title in self.titles:
            self.job_title_short.append(self._categorize_job_title(title))
    
    def scrape_jobs(self, job_keyword, n_pages):
        for i in range(1, n_pages+1):
            url = f'https://www.adzuna.co.uk/jobs/search?cty=permanent&loc=86384&q={job_keyword}&p={i}'
            browser = webdriver.Firefox(options=options)
            browser.get(url)

            titleelem_list = browser.find_elements(By.CSS_SELECTOR, 'a[data-js="jobLink"]')

            for title in titleelem_list:
                if title.text:
                    self.titles.append(title.text)

            companyelem_list = browser.find_elements(By.CSS_SELECTOR, 'div.ui-company')

            for company in companyelem_list:
                self.companies.append(company.text)

            sal_list = browser.find_elements(By.CSS_SELECTOR, 'div.ui-salary')

            for sal in sal_list:
                match = re.search(r'(£[\d,]+)', sal.text)
                if match:
                    value = match.group(1)
                    value = value.replace(',', '')
                    self.salary.append(value)
                    s_rate = self._salary_rate(value)
                    self.salary_rate.append(s_rate)
                    self.schedule.append("Full-time")
                else:
                    self.salary.append("Competitive Salary")
                    self.salary_rate.append("yearly")
                    self.schedule.append("Full-time")

            locaelem_list = browser.find_elements(By.CSS_SELECTOR, 'div.ui-location')
            for loca in locaelem_list:
                temp = loca.text
                res = ''
                for i in range(len(temp)):
                    if temp[i] == ' ' and i > 0 and temp[i-1] == ' ' or temp[i] == '+':
                        break
                    else:
                        res += temp[i]
                if res:
                    cleaned = re.sub(r'[\r\n]+', '', res)
                    self.locations.append(cleaned.rstrip(','))

            urlelem_list = browser.find_elements(By.CSS_SELECTOR, 'a[data-js="jobLink"]')
            for u in urlelem_list:
                
                temp = u.get_attribute('href')
                if self.urls and temp != self.urls[-1]:
                    self.urls.append(temp)
                elif not self.urls:
                    self.urls.append(temp)
                else:
                    continue
            for title, company, loca, u, sal in zip(self.titles, self.companies, self.locations, self.urls, self.salary):
                print(title)
                print(company)
                print(loca)
                print(u)
                print(sal)
                print("="*50)

            browser.quit()
            

    def jd_extraction(self):
        browser = webdriver.Firefox(options=options)
        for u in self.urls:
            try:
                browser.get(u)
                time.sleep(np.random.uniform(3, 5))
                descelem = browser.find_element(By.CSS_SELECTOR, "div.ui-foreign-click-description")
                if descelem:
                    cleaned_desc = self.clean_text(descelem.text)
                    self.job_description.append(cleaned_desc)      
                    skills = self._extract_skills(cleaned_desc)
                    self.job_skills.append(skills)
                    degree = self._extract_degree(cleaned_desc)
                    self.degree.append(degree)
                    health_ins = self._extract_job_health_insurance_info(cleaned_desc)
                    self.health_insurance.append(health_ins)
                    remote = self._extract_job_work_from_home(cleaned_desc)
                    self.work_from_home.append(remote)

            except:
                print(f"Failed to load job description for {u}")
                self.job_description.append("Description not available")
                self.job_skills.append("N/A")
                self.degree.append("N/A")
                self.health_insurance.append("N/A")
                self.work_from_home.append("N/A")
                time.sleep(np.random.uniform(3, 5))

        browser.quit()

    def _save_to_csv(self):
        import csv
        try:
            with open(self.output_filename + '.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Title_Short' 'Company', 'Location', 'URL', 'Job Description', 'Skills', 'Salary', 'Job_Health_Insurance', 'Degree', 'Remote Work', 'Job_via', 'Job_Schedule', 'Salary_rate', 'City'])
                for title, title_short, company, loca, u, desc, skills, salary, hinsurance, degree, remote, schedule, rate in zip(self.titles, self.job_title_short, self.companies, self.locations, self.urls, self.job_description, self.job_skills, self.salary, self.health_insurance, self.degree, self.work_from_home, self.schedule, self.salary_rate):
                    writer.writerow([
                        title.strip(),
                        title_short.strip(),
                        company.strip(),
                        loca.strip(),
                        u.strip(),
                        desc.strip(),
                        skills.strip(),
                        salary.strip(),
                        hinsurance.strip(),
                        degree.strip(),
                        remote.strip(),
                        'Adzuna',
                        schedule.strip(),
                        rate.strip(),
                        'London'
                    ])
            print(f"Saved to {self.output_filename}")
        except Exception as e:
            print(f'Error saving to csv: {e}')
    
    def _save_to_json(self):
        data = []
        json_filename = self.output_filename + '.json'
        for title, title_short, company, loca, u, desc, skills, salary, hinsurance, degree, remote, schedule, rate in zip(self.titles, self.job_title_short, self.companies, self.locations, self.urls, self.job_description, self.job_skills, self.salary, self.health_insurance, self.degree, self.work_from_home, self.schedule, self.salary_rate):
            data.append({
                'title': title.strip(),
                'title_short': title_short.strip(),
                'company': company.strip(),
                'locations': loca.strip(),
                'job_url': u.strip(),
                'job_description': desc.strip(),
                'skills': skills.strip(),
                'salary': salary.strip(),
                'health_insurancce': hinsurance.strip(),
                'degree': degree.strip(),
                'work_from_home': remote.strip(),
                'job_via': 'Adzuna',
                'schedule': schedule.strip(),
                'salary_rate': rate.strip(),
                'city': 'London'
                
            })
        
        with open(json_filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Saved to {json_filename}")

    def _save_to_excel(self):
        excel_filename = self.output_filename + '.xlsx'
        
        new_df = pd.DataFrame({
            'Title': [title.strip() for title in self.titles],
            'Title_Short':[st.strip() for st in self.job_title_short],
            'Company': [company.strip() for company in self.companies],
            'Location': [loca.strip() for loca in self.locations],
            'URL': [url.strip() for url in self.urls],
            'Job Description': [desc.strip() for desc in self.job_description],
            'Skills': [skills.strip() for skills in self.job_skills],
            'Salary': [sal.strip() for sal in self.salary],
            'Job_Health_Insurance': [j.strip() for j in self.health_insurance],
            'Degree': [d.strip() for d in self.degree],
            'Remote Work': [r.strip() for r in self.work_from_home],
            'Job_via': 'Adzuna',
            'Job_Schedule': [js.strip() for js in self.schedule],
            'Salary_rate': [rate.strip() for rate in self.salary_rate],
            'City': 'London'
        })
        
        if os.path.exists(excel_filename):
            existing_df = pd.read_excel(excel_filename, engine='openpyxl')
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['Title', 'Company'], keep='first')
            combined_df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f'Appended to {excel_filename}. Total jobs: {len(combined_df)}')
        else:
            new_df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f'Created {excel_filename} with {len(new_df)} jobs')

    def _send_to_pipeline(self):
            webhook_url = "https://primary-production-dacdb.up.railway.app/webhook/adzuna"
            all_jobs=[]
            for item in zip(self.titles, self.companies, self.locations, self.urls, 
                            self.job_skills, self.salary, self.work_from_home, self.schedule):
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
                    "job_via": "Adzuna",
                    "city": "London"
                }
                all_jobs.append(job)
            try:
                payload = {"jobs": all_jobs}
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                print(f"✓ Sent: {len(all_jobs)} at {company.strip()}")
            except requests.exceptions.RequestException as e:
                print(f"✗ Failed to send batch: {e}")

if __name__ == '__main__':
    scraper = AdzunaScraper()
    job_keyword = "Data Analyst"
    page_number = 1
    scraper.scrape_jobs(job_keyword, page_number)
    scraper.jd_extraction()

    scraper._shortening_titles()

    print(len(scraper.titles))
    print(len(scraper.companies))
    print(len(scraper.urls))
    print(len(scraper.job_description))
    print(len(scraper.job_skills))
    print(len(scraper.job_title_short))
    print(len(scraper.locations))
    print(len(scraper.salary))
    print(len(scraper.degree))
    print(len(scraper.health_insurance))
    print(len(scraper.work_from_home))
    print(len(scraper.schedule))
    print(len(scraper.salary_rate))
    scraper._save_to_csv()
    scraper._save_to_json()
    scraper._save_to_excel()   
    scraper._send_to_pipeline() 