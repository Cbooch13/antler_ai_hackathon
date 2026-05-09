from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.data import router as data_router
from app.routers.health import router as health_router
from app.routers.intake import router as intake_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Austin Build Feasibility API",
        version="0.1.0",
        description="Backend API for staged lot feasibility, compliance, and design workflows.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(data_router)
    app.include_router(health_router)
    app.include_router(intake_router)
    return app


app = create_app()
