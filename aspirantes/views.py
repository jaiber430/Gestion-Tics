from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404

import os
from django.conf import settings
from aspirantes.utils import eliminar_carpetas_vencidas, combinar_pdfs

from django.core.files.base import ContentFile

# from .pdf_processor import process_pdf_image

# Importar datos de los modulos requeridos
from Cursos.models import Aspirantes, Solicitud, Caracterizacion, Tipoidentificacion

from datetime import datetime

# IMPORTS LOCALES PARA NO MODIFICAR EL TOPE DEL ARCHIVO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from django.contrib import messages
# Importar path desde pathlib para elimnar archivos (Forma moderna)
from pathlib import Path

def formulario_aspirantes(request, idsolicitud):

    solicitud = get_object_or_404(Solicitud, idsolicitud=idsolicitud)

    # Asegurarse de que no se puedan voler a registrar aspirantes una vez se cumpla la cantidad
    cerrar_inscripciones = Aspirantes.objects.filter(solicitudinscripcion=solicitud).count()
    if cerrar_inscripciones >= solicitud.cupo:
        # En lugar de un 404, mostrar un mensaje en la misma vista y ocultar el formulario
        messages.error(request, 'Los cupos ya están completos para esta solicitud.')
        return render(request, 'forms/formulario_aspirantes.html', {
            'solicitud': solicitud,
            'cupo_completo': True,
        })

    caracterizacion = Caracterizacion.objects.all()
    tipo_documento = Tipoidentificacion.objects.all()

    return render(request, 'forms/formulario_aspirantes.html', {
        'tipos_identificacion': tipo_documento,
        'caracterizaciones': caracterizacion,
        'solicitud': solicitud,
        'cupo_completo': False,
    })

def registro_aspirante(request):
    if request.method == "POST":

        try:
            nombres = request.POST.get('nombres').upper()
            apellidos = request.POST.get('apellidos')
            caracterizacion_id = request.POST.get('tipo_caracterizacion')
            telefono = request.POST.get('telefono')
            pdf = request.FILES.get('pdf_documento')
            tipo_documento_id = request.POST.get('tipo_documento')
            identificacion = request.POST.get('numero_identificacion')
            correo = request.POST.get('correo')
            solicitud_inscripcion = request.POST.get('idsolicitud')

            fecha_registro = datetime.now()

            # Bloquear registro si el cupo ya está completo (validación del lado servidor)
            try:
                solicitud_obj = Solicitud.objects.get(idsolicitud=solicitud_inscripcion)
            except Solicitud.DoesNotExist:
                messages.error(request, 'La solicitud no existe.')
                return redirect('formularioaspirantes', idsolicitud=solicitud_inscripcion)

            conteo_actual = Aspirantes.objects.filter(solicitudinscripcion=solicitud_obj).count()
            if conteo_actual >= solicitud_obj.cupo:
                messages.error(request, 'Los cupos ya están completos para esta solicitud.')
                return redirect('formularioaspirantes', idsolicitud=solicitud_inscripcion)

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

            # Nombre del archivo usando el número de identificación
            nombre_archivo = f"{identificacion}.pdf"
            direccion_archivo = os.path.join(pdf_aspirantes, nombre_archivo)

            # Validar que no exista ya un PDF con ese documento
            if os.path.exists(direccion_archivo):
                messages.error(request, 'Ya existe un aspirante registrado con este documento.')
                return redirect('formularioaspirantes', idsolicitud=solicitud_inscripcion)

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
                telefono=int(telefono),
                pdf=ruta_relativa_pdf,  # ruta relativa para FileField
                tipoidentificacion=id_tipo_documento,
                numeroidentificacion=int(identificacion),
                correo=correo,
                fecha=fecha_registro,
                solicitudinscripcion=id_solicitud_preinscripcion,
            )

            # Primero ordenas los aspirantes
            aspirantes = Aspirantes.objects.filter(
                solicitudinscripcion=id_solicitud_preinscripcion
            ).order_by("idaspirante")

            # Luego haces el conteo
            total_aspirantes = aspirantes.count()

            if total_aspirantes >= id_solicitud_preinscripcion.cupo:
                combinar_pdfs(pdf_aspirantes)

                # ==============================================================
                # Generar archivo Excel con base en los aspirantes
                # ==============================================================

                # Asegurarse de que el id este siendo enviado cuando se oprima el boton de descargar
                solicitud = id_solicitud_preinscripcion

                # Consulta para obtener el nombre del programa relacionado con la solicitud
                programa = solicitud.codigoprograma  # Ya tienes la solicitud, accedes directo al FK
                nombre_programa = programa.nombreprograma  # Mostrar el nombre del programa

                # Crear un nuevo archivo de excel en blanco
                nuevo_archivo = Workbook()
                hoja = nuevo_archivo.active  # Seleccionar la hoja del excel (Primera por defecto)
                hoja.title = f"Aspirantes Inscritos"  # Colocar nombre a esa hoja

                # 🔹 Insertar campo de título que abarca todas las columnas (A1:G1)
                hoja.merge_cells("A1:G1")  # Unir desde A1 hasta G1
                celda = hoja["A1"]
                celda.value = "FORMATO PARA LA INSCRIPCIÓN DE ASPIRANTES EN SOFIA PLUS v1.0"

                # Estilo de celda del título
                celda.font = Font(bold=True, color="FFFFFF")  # Negrita y texto blanco
                celda.fill = PatternFill(start_color="66BB6A", end_color="66BB6A", fill_type="solid")  # Fondo verde medio
                celda.alignment = Alignment(horizontal="center", vertical="center")  # Centrado

                # Ajustar altura de la fila 1
                hoja.row_dimensions[1].height = 28.5

                # -----------------------------------------------------------
                # Fila de encabezados (fila 2) - 7 columnas exactas (A2:G2)
                # -----------------------------------------------------------
                encabezados = [
                    'Resultado del Registro(Reservado para el sistema)',
                    'Tipo de identificacion',
                    'Numero de identificacion',
                    'Código de ficha',
                    'Tipo población aspirantes',
                    '',
                    'Codigo empresa (solo si la ficha es cerrada)'
                ]
                hoja.append(encabezados)

                # Ajustar altura de la fila 2 (encabezados)
                hoja.row_dimensions[2].height = 51

                # Opcional: dar estilo a encabezados (negrita y centrado)
                for col_idx in range(1, len(encabezados) + 1):
                    cell = hoja.cell(row=2, column=col_idx)
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # Consulta para obtener los aspirantes relacionados con la solicitud
                aspirantes = Aspirantes.objects.filter(
                    solicitudinscripcion=solicitud
                ).order_by("numeroidentificacion")


                # Agregar filas de datos (7 columnas por fila) para cada aspirante
                for agregar in aspirantes:
                    # Nombre del tipo de población
                    caracterizacion = agregar.idcaracterizacion
                    tipo_caracterizacion = caracterizacion.caracterizacion if caracterizacion else ''

                    # Nombre del tipo de identificacion
                    identificacion_tipo = agregar.tipoidentificacion
                    tipo_identificacion = identificacion_tipo.tipoidentificacion if identificacion_tipo else ''

                    # Buscar el NIT de la empresa desde la solicitud
                    empresa = agregar.solicitudinscripcion.idempresa
                    if empresa is not None:
                        mostrar_empresa = empresa.nitempresa
                    else:
                        mostrar_empresa = ''

                    # Agregar fila de datos del aspirante (7 columnas exactas)
                    hoja.append([
                        '',  # Resultado del Registro (vacío por ahora)
                        tipo_identificacion,
                        agregar.numeroidentificacion,
                        '',  # Código de ficha (no definido aún)
                        tipo_caracterizacion,
                        '',  # Columna vacía como en encabezado
                        mostrar_empresa
                    ])

                # -----------------------------------------------------------
                # Crear carpeta donde se van a almacenar los formatos masivos
                # -----------------------------------------------------------
                nombre_archivo_excel = f"formato_inscripcion_{solicitud.idsolicitud}.xlsx"
                carpeta_excel = os.path.join(settings.MEDIA_ROOT, 'excel')
                os.makedirs(carpeta_excel, exist_ok=True)

                # Dirección donde se encuentra el archivo
                directorio_excel = os.path.join(carpeta_excel, nombre_archivo_excel)

                # Guardar archivo Excel
                nuevo_archivo.save(directorio_excel)
                # -----------------------------------------------------------

            messages.success(request, 'Te has preinscrito exitosamente')
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

def updateCandidate(request, idSolicitud, numDoc):

    if request.method != "POST":
        raise Http404()

    aspirante = get_object_or_404(
        Aspirantes,
        numeroidentificacion=numDoc,
        solicitudinscripcion=idSolicitud
    )

    try:
        # Documento antiguo
        doc_antiguo = aspirante.numeroidentificacion

        # Documento nuevo
        doc_nuevo = int(request.POST.get('numero_identificacion'))

        aspirante.nombre = request.POST.get('nombres').upper()
        aspirante.apellido = request.POST.get('apellidos').upper()
        aspirante.tipoidentificacion_id = int(request.POST.get('tipo_documento'))
        aspirante.numeroidentificacion = doc_nuevo

        # Guardar solo los campos editados (NO el pdf)
        aspirante.save(update_fields=[
            'nombre',
            'apellido',
            'tipoidentificacion',
            'numeroidentificacion'
        ])
        # Ruta del pdf
        basePath = Path(settings.MEDIA_ROOT)
        folderPdf = basePath / "pdf" / f"solicitud_{idSolicitud}"

        pdfOld = folderPdf / f"{doc_antiguo}.pdf"
        newPdf = folderPdf / f"{doc_nuevo}.pdf"

        # Renombrar solo el pdf del aspirante relacionado
        if doc_antiguo != doc_nuevo and pdfOld.exists():
            pdfOld.rename(newPdf)

        messages.success(request, "Aspirante actualizado correctamente")

    except Exception as e:
        messages.error(request, f"Error al actualizar aspirante: {e}")

    return redirect('consultas_instructor')

# Eliminar aspirante
def removeApplicant(request, idSolicitud, numDoc):

    folderName = Path(settings.MEDIA_ROOT)

    try:
        # Eliminar pdf del aspirante
        deleteDocumentFile = folderName / "pdf" / f"solicitud_{idSolicitud}" / f"{numDoc}.pdf"
        if deleteDocumentFile.exists():
            deleteDocumentFile.unlink()

        # Eliminar aspirante de la DB
        eliminado, _ = Aspirantes.objects.filter(
            numeroidentificacion=numDoc,
            solicitudinscripcion=idSolicitud
        ).delete()

        if eliminado == 0:
            messages.warning(request, "No se encontró el aspirante para eliminar")
            return redirect('consultas_instructor')

        # Eliminar pdf combinado
        deleteCombinedPdf = folderName / "pdf" / f"solicitud_{idSolicitud}" / "combinado.pdf"
        if deleteCombinedPdf.exists():
            deleteCombinedPdf.unlink()

        # Eliminar masivo excel
        deleteExcel = folderName / "excel" / f"formato_inscripcion_{idSolicitud}.xlsx"
        if deleteExcel.exists():
            deleteExcel.unlink()

        messages.success(request, "Aspirante eliminado correctamente")

    except Exception as e:
        messages.error(request, f"Error al eliminar aspirante: {e}")

    return redirect('consultas_instructor')
