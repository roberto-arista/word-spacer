from fastapi import Request
from fastapi.responses import Response
from fastapi.routing import APIRouter
from jinja2_fragments.fastapi import Jinja2Blocks

from app.config import settings
from app.typesetting import typeset

router = APIRouter()
templates = Jinja2Blocks(directory=settings.TEMPLATE_DIR)


@router.get("/")
def home(request: Request):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("index.html", context)


@router.get("/words/{word}")
def get_word(request: Request, word: str) -> Response:
    svg_path = typeset(word)
    context = {
        "request": request,
        "svg_path": svg_path,
        "word": word,
    }
    return templates.TemplateResponse("word.html", context)
