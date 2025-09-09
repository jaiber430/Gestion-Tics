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
    if cerrar_inscripciones >= solicitud.cupo:
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

            # Subcarpeta con el id de la solicitud
            carpeta_solicitud = f"solicitud_{instructor.idsolicitud}"
            pdf_aspirantes = os.path.join(settings.MEDIA_ROOT, 'pdf', carpeta_solicitud)
            os.makedirs(pdf_aspirantes, exist_ok=True)

            # Contador para el nombre del archivo
            contador = 1
            while True:
                nombre_archivo = f"PDF_{contador}.pdf"
                direccion_archivo = os.path.join(pdf_aspirantes, nombre_archivo)
                if not os.path.exists(direccion_archivo):
                    break
                contador += 1

            # Guardar PDF manualmente en la carpeta creada
            with open(direccion_archivo, 'wb+') as destino:
                for chunk in pdf.chunks():
                    destino.write(chunk)

            # Crear aspirante y asignar ruta relativa correcta en el campo pdf
            ruta_relativa_pdf = os.path.join('pdf', carpeta_solicitud, nombre_archivo)
            Aspirantes.objects.create(
                nombre=nombres,
                apellido=apellidos,
                idcaracterizacion=id_tipo_caracterizacion,
                telefono=telefono,
                pdf=ruta_relativa_pdf,  # ruta relativa para FileField
                tipoidentificacion=id_tipo_documento,
                numeroidentificacion=identificacion,
                correo=correo,
                fecha=fecha_registro,
                solicitudinscripcion=id_solicitud_preinscripcion,
            )

            # Combinar PDFs si se completa el cupo
            total_aspirantes = Aspirantes.objects.filter(solicitudinscripcion=id_solicitud_preinscripcion).count()
            if total_aspirantes >= id_solicitud_preinscripcion.cupo:
                combinar_pdfs(pdf_aspirantes)

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
