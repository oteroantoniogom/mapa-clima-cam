# 🚀 Despliegue Profesional: GitHub + Hosting Gratis

Esta es la forma más profesional de gestionar tu proyecto: el código vive en **GitHub** y se despliega automáticamente en **Hugging Face Spaces**.

## Paso 1: Subir código a GitHub

1. **Crea un Repositorio**: En GitHub, pulsa el botón `+` -> `New repository`. Llámalo `mapa-clima-cam`.
2. **Sube los archivos**:
   - Puedes arrastrar todos los archivos de esta carpeta a la web de GitHub (excepto `node_modules` y `.venv`).
   - *Tip*: El archivo `.gitignore` que he creado evitará que subas basura innecesaria.

## Paso 2: Conectar con Hugging Face (Hosting Gratis)

1. Ve a [huggingface.co/new-space](https://huggingface.co/new-space).
2. **Nombre**: El que quieras.
3. **SDK**: Selecciona **Docker**.
4. **IMPORTANTE**: No selecciones "Blank". Busca abajo el botón que dice **"Sync with GitHub repository"**.
5. Selecciona tu repositorio de GitHub `mapa-clima-cam`.
6. **Visibilidad**: Public (recomendado para que el despliegue automático funcione sin configurar tokens).

## Paso 3: ¡Magia! ✨

A partir de ahora, cada vez que hagas un cambio en GitHub, Hugging Face lo detectará y actualizará la web automáticamente en un par de minutos.

---

### Detalles Técnicos del Mapa:
- El servidor corre en el puerto `7860`.
- Las imágenes generadas se auto-borran cada hora.
- No hay límites de uso costosos (es el tier gratuito de HF).
