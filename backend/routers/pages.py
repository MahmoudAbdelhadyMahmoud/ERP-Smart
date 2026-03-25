from fastapi import APIRouter, Response, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(tags=['Pages'])

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@router.get("/")
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/add-expense")
def read_add_expense(request: Request):
    # This might still be needed if the user navigates directly, 
    # but we should probably redirect to /#register_expense
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/opening-balances")
def read_opening_balances(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
