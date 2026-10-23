import serpapi
from pydantic import BaseModel
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
class job_details(BaseModel):
    company_name: str
    company_details: str
    stipend: int| None
    company_contact: str| None
    duration: str| None
    Location: str|None
    Role_desc: str
    comp_url: str|None
client=serpapi.Client(api_key=os.getenv())
SKIP_FETCH = ("linkedin.com", "glassdoor.com", "ambitionbox.com",
              "facebook.com", "youtube.com", "instagram.com")

def build_queries(job: job_details) -> dict[str, str]:
    
    c = f'"{job.company_name}"' # To get the company name from the variable job.company_name
    loc = job.Location or "" # TO get the location if node then ""
    domain = urlparse(job.comp_url).netloc.removeprefix("www.") if job.comp_url else None #To get the company url

    qr = {
        "linkedin_page": f'{c} site:linkedin.com/company',
        "reviews":       f'{c} (site:glassdoor.com OR site:ambitionbox.com)',
        "registry":      f'{c} CIN OR "company registration" India',
    }
    if domain:
        # anchored on the domain, so no name collisions
        qr["scam_reports"] = f'"{domain}" (scam OR fraud OR "fake offer")'
    else:
        qr["official_site"] = f'{c} official website {loc}'
        qr["scam_reports"]  = f'{c} {loc} (scam OR fraud OR "fake offer" OR "registration fee")'
    if job.company_contact:
        qr["contact_check"] = f'"{job.company_contact}" (scam OR fraud)'
    return qr

def run_search(name, query):
    try:
        res = client.search(engine="google", q=query, gl="in", hl="en", num=5)
        organic = res.get("organic_results", [])[:5]
        return name, [
            {"title": r.get("title", ""), "link": r.get("link", ""),
             "snippet": r.get("snippet", ""), "date": r.get("date")}
            for r in organic
        ]
    except Exception:
        return name, []          # inconclusive, never a red flag

def is_relevant(r, job):
    text = (r["title"] + " " + r["snippet"] + " " + r["link"]).lower()
    return job.company_name.lower() in text

def fetch_page(url):
    if any(d in url for d in SKIP_FETCH):
        return None
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer"]):
            t.decompose()
        return {
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "text": soup.get_text(" ", strip=True)[:2000],
        }
    except requests.RequestException:
        return None

def search_all(job: job_details) -> dict[str, list[dict]]:
    queries = build_queries(job)

    # 1. all searches in parallel
    with ThreadPoolExecutor(max_workers=5) as ex:
        results = dict(ex.map(lambda kv: run_search(*kv), queries.items())) # Queries is a dictionary and we are using the items() method to get the key-value pairs of the dictionary.
#Lambda function is used to pass the key-value pairs to run_search function
#*kv seperates the key value pairs and passes them as arguments to run_search function
#ex.map() is a thread pool can run multiple searches in parallel.
#dict() is used to convert the results into a dictionary where the key is the name of the search and the value is the list of results.
    # 2. filter BEFORE fetching: only relevant results, top 2 per check
    for name, items in results.items():
        results[name] = [r for r in items if is_relevant(r, job)][:2]

    # 3. fetch the survivors in parallel
    targets = [(name, r) for name, items in results.items() for r in items]
    with ThreadPoolExecutor(max_workers=8) as ex:
        pages = list(ex.map(lambda t: fetch_page(t[1]["link"]), targets))
    for (name, r), page in zip(targets, pages):
        r["page"] = page          # None if blocked/failed, snippet still usable

    return results
