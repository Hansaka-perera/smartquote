from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from .database import Base, engine, SessionLocal, ROOT
from . import models
from .engines.default_systems import DEFAULT_SYSTEMS
from .sample_data import CATEGORIES
from .routers import catalog, calc, quotations, misc

SCHEMA_VERSION = 1


def init_db():
    """Create tables and seed non-sample configuration (categories + aluminium systems).
    NOTE: schema changes after v1 should go through Alembic (see README 'Migrations')."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for c in CATEGORIES:
            if not db.scalar(select(models.MaterialCategory).where(models.MaterialCategory.name == c)):
                db.add(models.MaterialCategory(name=c))
        for s in DEFAULT_SYSTEMS:
            if not db.scalar(select(models.AluminiumSystem).where(models.AluminiumSystem.code == s["code"])):
                db.add(models.AluminiumSystem(**s))
        if not db.get(models.Setting, "schema"):
            db.add(models.Setting(key="schema", value={"version": SCHEMA_VERSION}))
        db.commit()


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="SmartQuote Studio", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (catalog.router, calc.router, quotations.router, misc.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok"}


DIST = ROOT / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
