from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from procurement_router import router as procurement_router
from routers import router

app = FastAPI(title="Energy Supply Chain Resilience API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for a hackathon demo, tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(procurement_router)


@app.get("/")
async def root():
    return {"status": "ok"}
