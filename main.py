# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Product Intelligence")
app.include_router(router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
