from fastapi import FastAPI
from pydantic import BaseModel
from model import funct
from websearch import search_all
class job_details(BaseModel):
    company_name: str
    company_details: str
    stipend: int| None
    company_contact: str| None
    duration: str| None
    Location: str|None
    Role_desc: str
    comp_url: str|None


app=FastAPI()

@app.get("/")
def func():
    return "Hello Mother Fucker I'm Back" 

@app.post("/get_job_details")
def get_job_details(det: job_details):
    return search_all(det)
    
