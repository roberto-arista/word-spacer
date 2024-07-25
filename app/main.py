from os import getenv
from pathlib import Path

import arel
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.helpers import lifespan
from app.routes import router, templates

env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(env_path)


def get_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, **settings.fastapi_kwargs)
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
    app.include_router(router)
    if _debug := getenv("DEBUG"):
        hot_reload = arel.HotReload(paths=[arel.Path(".")])

        app.add_websocket_route("/hot-reload", route=hot_reload, name="hot-reload")  # type: ignore
        app.add_event_handler("startup", hot_reload.startup)
        app.add_event_handler("shutdown", hot_reload.shutdown)

        templates.env.globals["DEBUG"] = _debug
        templates.env.globals["hot_reload"] = hot_reload

    return app


app = get_app()
