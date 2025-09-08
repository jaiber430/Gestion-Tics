from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404

import os 
from django.conf import settings
from aspirantes.utils import eliminar_carpetas_vencidas, combinar_pdfs

# Importar datos de los modulos requeridos
from Cursos.models import Aspirantes, Solicitud, Caracterizacion, Tipoidentificacion

from datetime import datetime

from django.contrib import messages
# Create your views here.

def formulario_aspirantes(request, idsolicitud):

    solicitud = get_object_or_404(Solicitud, idsolicitud=idsolicitud)

    # Asegurarse de que no se puedan voler a registrar aspirantes una vez se cumpla la cantidad
    cerrar_inscripciones = Aspirantes.objects.filter(solicitudinscripcion=solicitud).count()
    if cerrar_inscripciones == solicitud.cupo:
        raise Http404("Ya se alcanzó el cupo máximo de aspirantes.")

    caracterizacion = Caracterizacion.objects.all()
    tipo_documento = Tipoidentificacion.objects.all()

    return render(request, 'forms/formulario_aspirantes.html', {
        'tipos_identificacion': tipo_documento,
        'caracterizaciones': caracterizacion,
        'solicitud': solicitud,
    })


def registro_aspirante(request):
    if request.method == "POST":
        # 🔹 Limpieza automática de carpetas vencidas
        # eliminar_carpetas_vencidas()

        try:
            nombres = request.POST.get('nombres')
            apellidos = request.POST.get('apellidos')
            caracterizacion_id = request.POST.get('tipo_caracterizacion')
            telefono = request.POST.get('telefono')
            pdf = request.FILES.get('pdf_documento')
            tipo_documento_id = request.POST.get('tipo_documento')
            identificacion = request.POST.get('numero_identificacion')
            correo = request.POST.get('correo')
            solicitud_inscripcion = request.POST.get('idsolicitud')

            fecha_registro = datetime.now()

            # Validar duplicados correctamente y con redirect al mismo formulario
            duplicado = Aspirantes.objects.filter(
                telefono=telefono
            ).exists() or Aspirantes.objects.filter(
                numeroidentificacion=identificacion
            ).exists() or Aspirantes.objects.filter(
                correo=correo
            ).exists()

            if duplicado:
                messages.error(request, 'Las credenciales ya han sido registradas')
                return redirect('formularioaspirantes', idsolicitud=solicitud_inscripcion)

            # Obtener objetos relacionados
            id_tipo_caracterizacion = Caracterizacion.objects.get(idcaracterizacion=caracterizacion_id)
            id_tipo_documento = Tipoidentificacion.objects.get(idtipoidentificacion=tipo_documento_id)
            id_solicitud_preinscripcion = Solicitud.objects.get(idsolicitud=solicitud_inscripcion)

            # Crear carpeta con la solicitud para almacenar los pdf 
            instructor = id_solicitud_preinscripcion
            carpeta_destino = os.path.join(settings.MEDIA_ROOT, f"solicitud_{instructor.idsolicitud}")
            os.makedirs(carpeta_destino, exist_ok=True)

            # Guardar PDF
            pdf_path = os.path.join(carpeta_destino, pdf.name)
            with open(pdf_path, 'wb+') as destino:
                for chunk in pdf.chunks():
                    destino.write(chunk)

            # Crear aspirante
            Aspirantes.objects.create(
                nombre=nombres,
                apellido=apellidos,
                idcaracterizacion=id_tipo_caracterizacion,
                telefono=telefono,
                pdf=pdf.name,
                tipoidentificacion=id_tipo_documento,
                numeroidentificacion=identificacion,
                correo=correo,
                fecha=fecha_registro,
                solicitudinscripcion=id_solicitud_preinscripcion,
            )

            # Combinar PDFs si se completa el cupo
            total_aspirantes = Aspirantes.objects.filter(solicitudinscripcion=id_solicitud_preinscripcion).count()
            if total_aspirantes >= id_solicitud_preinscripcion.cupo:
                combinar_pdfs(carpeta_destino)

            messages.success(request, 'Te has registrado exitosamente')
            return redirect('formularioaspirantes', idsolicitud=solicitud_inscripcion)

        except Exception as e:
            messages.error(request, f'Error al registrarte: {e}')
            return redirect('formularioaspirantes', idsolicitud=request.POST.get('idsolicitud'))

    # GET request
    caracterizacion = Caracterizacion.objects.all()
    tipo_documento = Tipoidentificacion.objects.all()

    return render(request, 'forms/formulario_aspirantes.html', {
        'tipos_identificacion': tipo_documento,
        'caracterizaciones': caracterizacion,
    })
