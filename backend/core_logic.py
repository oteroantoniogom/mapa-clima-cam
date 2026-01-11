import os
import zipfile
import fiona
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger
import pymupdf4llm
from thefuzz import process
from unidecode import unidecode

def extraer_shp_desde_zip(zip_path: str, tmpdir: str) -> str:
    """
    Descomprime un .zip con un shapefile y devuelve la ruta al .shp extraído.
    """
    extract_path = os.path.join(tmpdir, "shp_descomprimido")
    os.makedirs(extract_path, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    # Buscar recursivamente el archivo .shp
    shp_files = []
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.endswith(".shp"):
                shp_files.append(os.path.join(root, file))
    
    if not shp_files:
        raise FileNotFoundError("No se encontró ningún archivo .shp en el ZIP.")
    
    # Preferir uno que no empiece por ._ (archivos basura de macOS)
    valid_shp = [f for f in shp_files if not os.path.basename(f).startswith("._")]
    return valid_shp[0] if valid_shp else shp_files[0]

def extraer_datos_pdf(pdf_path: str) -> pd.DataFrame:
    """
    Extrae la tabla de zonas climáticas del PDF usando pymupdf4llm (Markdown).
    Busca patrones de líneas que parezcan filas de datos: "Municipio Zona".
    
    Spanish climate zones are typically: A1, A2, A3, A4, B1, B2, B3, B4, C1, C2, C3, C4, D1, D2, D3, E1
    Or sometimes Roman numerals: I, II, III, IV, V
    """
    import re
    
    md_text = pymupdf4llm.to_markdown(pdf_path)
    lines = md_text.split('\n')
    
    logger.info(f"PDF convertido a Markdown, {len(lines)} líneas encontradas.")
    logger.debug(f"Primeras 500 chars: {md_text[:500]}")
    
    data = []
    
    # Regex patterns for Spanish climate zones
    # Pattern 1: Letter + Number (+ optional lowercase): A1, B3, D3, E1, α1, etc.
    # Pattern 2: Roman numerals: I, II, III, IV, V
    zona_pattern = re.compile(r'^([A-Eα-ε][1-4][a-z]?|I{1,3}V?|IV|V)$', re.IGNORECASE)
    
    for line in lines:
        # Clean markdown table delimiters
        clean_line = line.strip()
        if not clean_line or clean_line.startswith('#') or clean_line.startswith('---'):
            continue
        
        # Remove markdown table pipes
        clean_line = clean_line.replace('|', ' ').strip()
        clean_line = re.sub(r'\s+', ' ', clean_line)  # Normalize whitespace
        
        parts = clean_line.rsplit(maxsplit=1)
        if len(parts) == 2:
            muni, zona = parts
            zona = zona.strip().upper()
            
            # Validate zone format
            if zona_pattern.match(zona) and len(muni) > 2:
                data.append({"Municipio": muni.strip(), "Zona": zona})
    
    if not data:
        # Fallback: Try more aggressive regex on raw text
        logger.warning(f"Parseo simple falló. Intentando regex agresivo...")
        logger.warning(f"Preview MD: {md_text[:800]}")
        
        # Look for patterns like "Municipio Name   D3" anywhere in the text
        aggressive_pattern = re.compile(
            r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[a-záéíóúñA-ZÁÉÍÓÚÑ]+)*?)\s+([A-E][1-4][a-z]?)',
            re.MULTILINE
        )
        
        matches = aggressive_pattern.findall(md_text)
        for muni, zona in matches:
            if len(muni) > 3:  # Avoid false positives
                data.append({"Municipio": muni.strip(), "Zona": zona.strip().upper()})
    
    if not data:
        # Last resort: log what we found and fail gracefully
        sample = md_text[:1000].replace('\n', ' | ')
        raise ValueError(f"No se encontraron pares Municipio-Zona en el PDF. Contenido: {sample}")
    
    logger.info(f"Extraídos {len(data)} municipios del PDF")
    return pd.DataFrame(data)

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return unidecode(texto).lower().strip()

def unificar_datos(gdf: gpd.GeoDataFrame, df_pdf: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Une el GeoDataFrame con los datos del PDF usando Fuzzy Matching en nombres de municipios.
    """
    # Log all available columns for debugging
    logger.info(f"Columnas disponibles en SHP: {list(gdf.columns)}")
    
    # Sample values from string columns to help identify the name column
    for col in gdf.columns:
        if pd.api.types.is_string_dtype(gdf[col]):
            sample = gdf[col].dropna().head(3).tolist()
            logger.debug(f"Columna '{col}' ejemplos: {sample}")
    
    # Priority list of column names (Spanish shapefiles for municipalities)
    posibles_cols = [
        'NAMEUNIT', 'NOMBRE', 'MUNICIPIO', 'NOM_MUN', 'NM_MUN', 'MUNIC',
        'NAME', 'NMUN', 'DENOMINACI', 'ROTULO', 'TEXTO', 'ETIQUETA',
        'NOMBRE_MUN', 'NAMEUNI', 'MUNI_NAME'
    ]
    col_shp = next((c for c in posibles_cols if c.upper() in [x.upper() for x in gdf.columns]), None)
    
    # If found by name, get the actual case
    if col_shp:
        col_shp = next(c for c in gdf.columns if c.upper() == col_shp.upper())
    
    if not col_shp:
        # Fallback: find string column with longest average value (names are longer than codes)
        best_col = None
        best_avg_len = 0
        
        for col in gdf.columns:
            if col.lower() == 'geometry':
                continue
            if pd.api.types.is_string_dtype(gdf[col]):
                avg_len = gdf[col].dropna().astype(str).str.len().mean()
                logger.debug(f"Columna '{col}' longitud media: {avg_len:.1f}")
                if avg_len > best_avg_len:
                    best_avg_len = avg_len
                    best_col = col
        
        if best_col and best_avg_len > 3:  # Names should be longer than 3 chars on average
            col_shp = best_col
            logger.info(f"Usando columna '{col_shp}' (longitud media {best_avg_len:.1f}) para el cruce.")
    
    if not col_shp:
        raise ValueError(f"No se encontró columna de nombre de municipio en el Shapefile. Columnas: {list(gdf.columns)}")
        
    logger.info(f"Usando columna '{col_shp}' del Shapefile para el cruce.")

    # Crear mapa de mapeo fuzzy
    nombres_pdf = df_pdf["Municipio"].unique()
    mapa_nombres = {}
    
    for nombre_shp in gdf[col_shp].unique():
        if not isinstance(nombre_shp, str): continue
        
        # Buscar mejor coincidencia en PDF
        mejor_match, score = process.extractOne(nombre_shp, nombres_pdf)
        if score > 80: # Umbral de confianza
            mapa_nombres[nombre_shp] = mejor_match
        else:
            mapa_nombres[nombre_shp] = None # No asignado

    # Aplicar mapeo
    gdf["match_pdf"] = gdf[col_shp].map(mapa_nombres)
    
    # Merge
    gdf_final = gdf.merge(df_pdf, left_on="match_pdf", right_on="Municipio", how="left")
    gdf_final["zona_climatica"] = gdf_final["Zona"].fillna("No asignado")
    
    return gdf_final

def generar_mapa_coloreado(pdf_path: str, shp_path: str, tmpdir: str, geojson: bool = False):
    """
    Flujo principal de generación.
    """
    os.environ["SHAPE_RESTORE_SHX"] = "YES"

    # 1. Procesar SHP
    shp_real_path = extraer_shp_desde_zip(shp_path, tmpdir)
    logger.info(f"Shapefile extraído: {shp_real_path}")
    
    with fiona.Env():
        gdf = gpd.read_file(shp_real_path)

    if gdf.empty:
        raise ValueError("El shapefile está vacío.")

    # 2. Procesar PDF
    try:
        df_pdf = extraer_datos_pdf(pdf_path)
        logger.info(f"Extraídas {len(df_pdf)} filas del PDF.")
    except Exception as e:
        logger.error(f"Error leyendo PDF: {e}")
        # Continuar con mapa vacío/gris si falla PDF, para no romper todo el flujo? 
        # No, mejor fallar para que el usuario sepa.
        raise ValueError(f"Error leyendo el PDF: {e}")

    # 3. Cruzar datos
    gdf_final = unificar_datos(gdf, df_pdf)
    
    # 4. Generar Salida
    if geojson:
        return gdf_final.to_json()

    output_path = os.path.join(tmpdir, "mapa_climatico.png")
    
    # Plotting
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Zonas sin datos (gris)
    sin_datos = gdf_final[gdf_final["zona_climatica"] == "No asignado"]
    if not sin_datos.empty:
        sin_datos.plot(ax=ax, color="#e0e0e0", edgecolor="white", linewidth=0.5, label="Sin datos")
        
    # Zonas con datos
    con_datos = gdf_final[gdf_final["zona_climatica"] != "No asignado"]
    if not con_datos.empty:
        con_datos.plot(
            ax=ax, 
            column="zona_climatica", 
            legend=True, 
            cmap="viridis", 
            edgecolor="white", 
            linewidth=0.5,
            legend_kwds={'title': "Zona Climática"}
        )
    
    plt.title("Zonificación Climática por Municipio")
    plt.axis("off")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    return output_path

