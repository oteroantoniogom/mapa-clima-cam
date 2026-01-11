import os
import tempfile
import shutil
from fastapi import UploadFile
from loguru import logger
from core_logic import generar_mapa_coloreado

# Carpeta de subidas (Docker o Local)
UPLOADS_DIR = "/app/uploads" if os.path.exists("/app/uploads") else os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR, exist_ok=True)

def procesar_archivos(pdf: UploadFile, shp: UploadFile, geojson: bool = False) -> dict:
    tmpdir = tempfile.mkdtemp()
    try:
        # ✅ Guardar archivos subidos
        pdf_path = os.path.join(tmpdir, pdf.filename)
        shp_path = os.path.join(tmpdir, shp.filename)

        with open(pdf_path, "wb") as f:
            f.write(pdf.file.read())
        with open(shp_path, "wb") as f:
            f.write(shp.file.read())

        # ✅ Generar salida
        output = generar_mapa_coloreado(pdf_path, shp_path, tmpdir, geojson=geojson)

        if geojson:
            return {"geojson": output}

        # ✅ Copiar PNG a carpeta persistente
        filename = os.path.basename(output)
        final_path = os.path.join(UPLOADS_DIR, filename)
        shutil.copy(output, final_path)
        logger.info(f"PNG copiado a: {final_path}")
        return {"png": final_path}

    finally:
        # ✅ Borra solo el directorio temporal, no `uploads`
        shutil.rmtree(tmpdir, ignore_errors=True)
