"""
Demo API - CS2 Demo Upload and Processing
Author: adamguedesmtm
Created: 2025-02-21 15:15:42
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import aiofiles
from pathlib import Path
import uuid
from ...shared.stats.demo_manager import DemoManager

router = APIRouter()
demo_manager = DemoManager(
    cs_demo_manager_path="/usr/local/bin/cs-demo-manager",
    demos_dir="data/demos"
)

@router.post("/upload")
async def upload_demo(demo: UploadFile = File(...)):
    """Upload e processar uma demo do CS2"""
    try:
        if not demo.filename.endswith('.dem'):
            raise HTTPException(400, "Arquivo deve ser uma demo do CS2 (.dem)")

        demo_dir = Path("data/demos")
        demo_dir.mkdir(parents=True, exist_ok=True)

        unique_filename = f"{uuid.uuid4()}_{demo.filename}"
        file_path = demo_dir / unique_filename

        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await demo.read()
            await out_file.write(content)

        match_stats = await demo_manager.process_demo(str(file_path))
        
        if not match_stats:
            raise HTTPException(500, "Erro ao processar demo")

        return JSONResponse({
            "success": True,
            "match_id": match_stats.match_id,
            "stats": match_stats.dict()
        })

    except Exception as e:
        raise HTTPException(500, f"Erro ao processar upload: {str(e)}")

@router.get("/match/{match_id}")
async def get_match_stats(match_id: str):
    """Obter estatísticas de uma partida específica"""
    try:
        # Implementar busca no banco de dados
        pass
    except Exception as e:
        raise HTTPException(500, f"Erro ao buscar estatísticas: {str(e)}")

@router.get("/recent")
async def get_recent_matches(limit: int = 10):
    """Obter partidas recentes"""
    try:
        # Implementar busca no banco de dados
        pass
    except Exception as e:
        raise HTTPException(500, f"Erro ao buscar partidas recentes: {str(e)}")