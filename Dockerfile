# ── Imagen base ──────────────────────────────────────────────────────────────
# Django 6.x requiere Python >=3.12 (Requires-Python >=3.12 en PyPI).
FROM python:3.12-slim

# ── Dependencias del sistema para WeasyPrint + PyMySQL ───────────────────────
# WeasyPrint 68 necesita Pango, Cairo y GDK-Pixbuf para generar PDFs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    libffi8 \
    libxml2 \
    libxslt1.1 \
    fonts-liberation \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# ── Directorio de trabajo ─────────────────────────────────────────────────────
WORKDIR /app

# ── Instalar dependencias Python (capa de caché independiente del código) ─────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copiar código fuente ──────────────────────────────────────────────────────
COPY . .

# ── Crear directorios de runtime y normalizar entrypoint ─────────────────────
# sed corrige saltos de línea CRLF (Windows) → LF (Linux) por si el archivo
# fue editado en Windows antes de construir la imagen.
RUN mkdir -p /app/media /app/staticfiles \
    && sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# ── Puerto de la aplicación ───────────────────────────────────────────────────
EXPOSE 8000

# ── Punto de entrada: migraciones + admin + gunicorn ─────────────────────────
ENTRYPOINT ["/app/entrypoint.sh"]
