from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, documents, evaluation
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Chat Bot",
        description="A simple RAG (Retrieval-Augmented Generation) chat bot",
        version="1.0.0",
    )

    # CORS middleware (allows frontend to call API)
    cors_origins = (
        settings.CORS_ORIGINS.split(",")
        if settings.CORS_ORIGINS != "*"
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(documents.router, prefix="/documents", tags=["documents"])
    app.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])

    @app.get("/")
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "message": "RAG Chat Bot API",
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )







