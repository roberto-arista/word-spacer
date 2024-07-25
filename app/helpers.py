from contextlib import asynccontextmanager
from subprocess import run

from fastapi import FastAPI

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for FastAPI app. It will run all code before `yield`
    on app startup, and will run code after `yield` on app shutdown. This method
    runs a subprocess on app startup which is the equivalent of running the
    tailwindcss command `tailwindcss -i ./src/tw.css -o ./css/main.css`.

    Must be passed as a property of the FastAPI app. (app = FastAPI(lifespan=lifespan))

    """
    try:
        run(
            [
                "tailwindcss",
                "-i",
                str(settings.STATIC_DIR / "src" / "tw.css"),
                "-o",
                str(settings.STATIC_DIR / "css" / "main.css"),
            ]
        )
    except Exception as error:
        raise RuntimeError from error
    yield
