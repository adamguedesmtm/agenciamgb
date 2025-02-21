"""
Web Server - CS2 Stats Display System
Author: adamguedesmtm
Created: 2025-02-21 15:15:42
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path
import uvicorn
from .api import demos

app = FastAPI(
    title="CS2 Stats",
    description="Sistema de visualização de estatísticas do CS2",
    version="1.0.0"
)

# Configurar arquivos estáticos e templates
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Adicionar rotas da API
app.include_router(demos.router, prefix="/api/demos", tags=["demos"])

@app.get("/")
async def home(request: Request):
    """Página inicial com visão geral das estatísticas"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "CS2 Stats"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)