import os
import shutil
from datetime import datetime, timedelta
from django.conf import settings
from pypdf import PdfWriter

# Ruta dinámica para almacenar PDFs según el instructor (usuario de la solicitud)
def upload_to_dynamic(instance, filename):
    """
    Devuelve la ruta donde se guardará un PDF de un aspirante,
    en una carpeta específica para cada instructor.
    """
    instructor = instance.solicitudinscripcion.idusuario
    carpeta = f"solicitudes/solicitud_{instructor.nombre}_{instructor.apellido}"
    return os.path.join(carpeta, filename)


# Eliminar carpetas con más de 2 minutos de antigüedad
def eliminar_carpetas_vencidas(base_path=None):
    """
    Recorre todas las carpetas dentro de `solicitudes` y elimina
    aquellas cuya fecha de creación/modificación exceda el tiempo límite (2 minutos por defecto).
    """
    if base_path is None:
        base_path = os.path.join(settings.MEDIA_ROOT, "solicitudes")

    if not os.path.exists(base_path):
        return

    for carpeta in os.listdir(base_path):
        carpeta_path = os.path.join(base_path, carpeta)
        # Obtener la fecha de modificación de la carpeta
        tiempo_modificacion = datetime.fromtimestamp(os.path.getmtime(carpeta_path))
        if datetime.now() - tiempo_modificacion > timedelta(minutes=2):
            shutil.rmtree(carpeta_path)


# Combinar PDFs en un solo archivo cuando se llena el cupo
def combinar_pdfs(carpeta_path, output_filename="combinado.pdf"):
    """
    Combina todos los PDFs dentro de una carpeta en un solo archivo.
    """
    merger = PdfWriter()
    for archivo in os.listdir(carpeta_path):
        if archivo.endswith(".pdf") and archivo != output_filename:
            merger.append(os.path.join(carpeta_path, archivo))

    if merger.pages:
        output_path = os.path.join(carpeta_path, output_filename)
        with open(output_path, "wb") as f_out:
            merger.write(f_out)
        merger.close()
