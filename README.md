# 🌍 Guía de Despliegue - Mapa Climático

Esta aplicación ha sido refactorizada para ofrecer una experiencia web moderna y dos métodos de despliegue principales: **Paquete Autónomo (Docker)** y **Hosting Estático**.

## 🏗️ Arquitectura

- **Frontend**: Astro + React + Tailwind CSS (Carpeta `web/`)
- **Backend**: FastAPI + GeoPandas + SpaCy (Carpeta `backend/`)
- **Despliegue**: Docker (Monolito) o Estático + API Remota.

---

## 🚀 Opción 1: Ejecución Local (Paquete Autónomo)

Esta opción es ideal para ejecutar la aplicación en tu máquina local sin configuración compleja. Requiere **Docker Desktop**.

### Pasos:

1.  Abre una terminal en la carpeta raíz del proyecto.
2.  Ejecuta:
    ```bash
    docker-compose up --build
    ```
3.  Abre tu navegador y ve a: [http://localhost:8000](http://localhost:8000)

**Nota**: La primera vez tardará unos minutos en construir la imagen (descargar dependencias, compilar frontend). Las siguientes veces será instantáneo.

---

## ☁️ Opción 2: Hosting Estático (GitHub Pages / Vercel / Netlify)

Si deseas alojar la parte visual en internet, sigue estos pasos. Ten en cuenta que **aún necesitarás un backend corriendo** (en un servidor VPS, Render, Railway, o tu propia máquina expuesta) para procesar los archivos.

### 1. Construir el Frontend
Desde la carpeta `web/`:

```bash
cd web
pnpm install
pnpm build
```

Esto generará una carpeta `dist/` con los archivos HTML/JS/CSS listos para subir.

### 2. Configurar la URL del Backend
Por defecto, el frontend buscará el backend en `http://localhost:8000`. Si despliegas el backend en la nube (ej. en `https://api.mi-mapa.com`), puedes configurar esto de dos formas:

1.  **Interactiva**: En la app web, haz clic en el icono de engranaje ⚙️ y pega la URL de tu API.
2.  **Compilación**: Crea un archivo `web/.env` con el contenido:
    ```
    PUBLIC_BACKEND_URL=https://api.mi-mapa.com
    ```
    Y vuelve a ejecutar `pnpm build`.

---

## 🛠️ Desarrollo (Dev Mode)

Si deseas modificar el código:

1.  **Backend**:
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```
2.  **Frontend**:
    ```bash
    cd web
    pnpm dev
    ```
3.  Abre [http://localhost:4321](http://localhost:4321) (Frontend) y asegúrate de que el backend corra en el puerto 8000.

---

## 📦 Características Nuevas

- **Interfaz Moderna**: Diseño "Glassmorphism" con animaciones suaves.
- **Drag & Drop**: Carga de archivos intuitiva.
- **Validación**: Feedback visual inmediato.
- **Previsualización**: Vista previa del mapa generado sin recargar.
