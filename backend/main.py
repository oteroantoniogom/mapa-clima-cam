from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
import re

from proces import procesar_archivos, UPLOADS_DIR

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Mapa Climático API",
    description="Procesa PDF+SHP y genera un mapa climático en PNG y GeoJSON opcional.",
    version="1.3.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Configurable origins (use env var in production)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# File size limits (bytes)
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_SHP_SIZE = 100 * 1024 * 1024  # 100 MB

def sanitize_filename(filename: str) -> str:
    """Remove path traversal attempts and dangerous characters."""
    # Only allow alphanumeric, dots, dashes, underscores
    basename = os.path.basename(filename)
    return re.sub(r'[^\w\-\.]', '_', basename)

def cleanup_old_files():
    """Elimina archivos en UPLOADS_DIR con más de 1 hora de antigüedad."""
    try:
        ahora = time.time()
        for f in os.listdir(UPLOADS_DIR):
            f_path = os.path.join(UPLOADS_DIR, f)
            if os.path.isfile(f_path):
                if ahora - os.path.getmtime(f_path) > 3600:
                    os.remove(f_path)
                    logger.info(f"Cleanup: Eliminado archivo antiguo {f}")
    except Exception as e:
        logger.error(f"Error en cleanup: {e}")

async def validate_upload(file: UploadFile, max_size: int, allowed_extensions: list[str]) -> bytes:
    """Validate file size and extension, return content."""
    # Sanitize filename
    file.filename = sanitize_filename(file.filename)
    
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida: {ext}. Permitidas: {allowed_extensions}")
    
    # Read and check size
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"Archivo demasiado grande. Máximo: {max_size // (1024*1024)} MB")
    
    # Reset file position for later use
    await file.seek(0)
    return content

# ✅ Endpoint principal
@app.post("/api/procesar/")
@limiter.limit("10/minute")
async def procesar(
    request: Request,
    background_tasks: BackgroundTasks,
    pdf: UploadFile = File(...), 
    shp: UploadFile = File(...), 
    geojson: bool = False
):
    try:
        # Validate uploads
        await validate_upload(pdf, MAX_PDF_SIZE, [".pdf"])
        await validate_upload(shp, MAX_SHP_SIZE, [".zip"])
        
        result = procesar_archivos(pdf, shp, geojson)
        
        # Programar limpieza
        background_tasks.add_task(cleanup_old_files)

        if geojson:
            return JSONResponse(content=result["geojson"])
        else:
            return FileResponse(result["png"], media_type="image/png")

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Error interno procesando archivos")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ✅ Servir Frontend (Soporte Docker y Local)
static_path = os.path.join(os.path.dirname(__file__), "static")
local_static_path = os.path.join(os.path.dirname(__file__), "..", "web", "dist")

if os.path.exists(static_path):
    logger.info(f"Sirviendo frontend desde: {static_path}")
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
elif os.path.exists(local_static_path):
    logger.info(f"Sirviendo frontend desde: {local_static_path} (Entorno Local)")
    app.mount("/", StaticFiles(directory=local_static_path, html=True), name="static")
else:
    logger.warning("No se encontró la carpeta static ni ../web/dist. El frontend no se servirá.")
