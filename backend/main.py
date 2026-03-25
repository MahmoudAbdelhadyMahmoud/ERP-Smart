from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import expenses, warehouse, analytics, system, pages, costing
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Manager AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.include_router(pages.router)
app.include_router(expenses.router)
app.include_router(warehouse.router)
app.include_router(analytics.router)
app.include_router(system.router)
app.include_router(costing.router)
# app.include_router(stock_control.router) # REMOVED

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Mount the static directory at the root to cater for app.js, etc.
# This should be at the end so it doesn't shadow explicit routes.
app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")

