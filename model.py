from groq import Groq
from pydantic import BaseModel
import json
import serpapi
import re

serp_client=serpapi.Client(api_key="")

class job_details(BaseModel):
    company_name: str
    company_details: str
    stipend: int| None
    company_contact: str| None
    duration: str| None
    Location: str|None
    Role_desc: str
    comp_url: str|None

client=Groq(api_key="")


def funct(conten: job_details):
   # con=job_details(company_name=conten.company_name, company_details=conten.company_details, stipend=conten.stipend, company_contact=conten.company_contact, duration=conten.duration, Location=conten.Location, Role_desc=conten.Role_desc)
    
    
    val=""
    con = f"""
You are a company research assistant helping evaluate job opportunities.

Job details:
{json.dumps(conten.dict(), indent=2)}

Your task is to generate a research plan for investigating this company and job opportunity.

Research these areas:
1. Company overview and official website
2. Company legitimacy and reputation
3.  Check in their career website whether the posted job is in their site.
4. Also check if the company is listed in any job portals and if the job is posted there.
5. Also check whether any scams has been reported about the company or the job posting and also check whether anyone asking to pay for the role.

Generate 8-12 specific Google search queries that can help investigate these areas.

IMPORTANT:
- Do not evaluate the company yet.
- Do not answer the research questions.
- Generate search queries that can find evidence from different sources.
- Include the company name and role where relevant.
- Avoid repetitive queries.
- Return ONLY valid JSON. Do not include markdown or explanations.

Required JSON format:
{{
    "company": "company name",
    "role": "job role",
    "research_queries": [
        {{
            "category": "company_overview",
            "query": "company name official website and services"
        }},
        {{
            "category": "employee_reviews",
            "query": "company name employee reviews work culture"
        }}
    ]
}}
"""
    #Here we will get the company details and send it to the LLm to get the research plan and fetch the data from google and return the data to the user in a structured format
    #con=json.dumps(conten.dict())+"Could you evaluate the above job details and provide a summary of the company, stipend, duration, location, and role description in a concise manner? Not from the data I have given could you research about thhew companiy in google and across all the sites what they are saying about the company and people who are working iint he company and what they are saying about the company and the work culture and the salary and the benefits and the perks and the growth opportunities and the work life balance and the management and the leadership and the vision and the mission and the values and the ethics and the social responsibility and the sustainability and the innovation and the technology and the products and services and the customers and clients and partners and competitors and market position and reputation and brand image and marketing strategy and sales strategy and distribution strategy and pricing strategy and financial performance and stock performance and investor relations and corporate governance and legal compliance and risk management and crisis management Also now ypou dont need to return answer instead i want you tao ask the data you need that i would surf inthe google and return the answer to you so you dont need to make a general conclusion"
    complete=client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
        {    "role": "user",
            "content": con
        }],
        temperature=0.0,
        max_completion_tokens=2048,
        top_p=1.0,
        reasoning_effort="medium",
        stream=True,
        stop=None
    )




    for chunk in complete:
        content=chunk.choices[0].delta.content
        if content is not None:
            val+=content
    print(val)
    val = val.strip()
#Val is the responnse from LLM which is in json format and we will parse it to get the research plan and then we will use the research plan to search for the data in google and return the data to the user in a structured format
# Remove markdown code fences if the model adds them
    val = re.sub(r"^```(?:json)?\s*|\s*```$", "", val)

    try:
        research_plan = json.loads(val) # converts string into dictionary
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM did not return valid JSON: {e}\nOutput: {val}"
        )

    if "research_queries" not in research_plan:
        raise ValueError("Missing research_queries in the LLM output")
    #research_plan = json.loads(val)
    all_results = []
    seen_urls = set()

    for item in research_plan["research_queries"]:

        query = item["query"]
        category = item["category"]

        print(f"\nSearching: {query}")

        response = serp_client.search(
            engine="google",
            q=query,
            num=5
        )

        for result in response.get("organic_results", []):

            link = result.get("link")

            if not link or link in seen_urls:
                continue

            seen_urls.add(link)

            evidence = {
                "category": category,
                "query": query,
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "link": link
            }

            all_results.append(evidence)

            print(f"Category: {category}")
            print(f"Title: {evidence['title']}")
            print(f"Snippet: {evidence['snippet']}")
            print(f"Link: {link}")
            print("-" * 80)

