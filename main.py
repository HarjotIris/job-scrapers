import subprocess
import sys

# Run all 4 scrapers
scrapers = [#-job_keyword AI --number_of_pages 10 --format all
    ("reed_scraper.py", "--job_keyword", "AI", "--number_of_pages", "10", "--format", "all"),
    ("linkedin_scraper.py", "--job_keyword", "AI", "--format", "all"),
    ("cv_library_scraper.py", "--job_keyword", "AI", "--number_of_pages", "10", "--format", "all"),
    ("adzuna_scraper.py",),  # No CLI arguments
]

for scraper_args in scrapers:
    scraper = scraper_args[0]
    args = list(scraper_args[1:])
    print(f"\n Running {scraper}...")
    result = subprocess.run([sys.executable, scraper] + args)
    if result.returncode != 0:
        print(f" Failed: {scraper}")
    else:
        print(f" Completed: {scraper}")