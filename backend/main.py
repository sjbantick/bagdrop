"""BagDrop FastAPI backend"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cache import close_cache, init_cache
from database import init_db
from routers import intelligence, listings, markets, ops, watchlists
from scheduler import create_scheduler, run_all_scrapers

scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    print("Database initialized")
    await init_cache()
    scheduler.start()
    print("Scheduler started — scraping every 4 hours")
    asyncio.create_task(run_all_scrapers())
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await close_cache()


app = FastAPI(title="BagDrop API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(markets.router)
app.include_router(intelligence.router)
app.include_router(watchlists.router)
app.include_router(ops.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from config import settings
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
