from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, FileResponse,  HttpResponse
from django.template.loader import render_to_string
from Cursos.models import (
    Usuario, Solicitud, Programaformacion, Horario, Modalidad, 
    Departamentos, Municipios, Empresa, Programaespecial, Ambiente,
    Aspirantes, Caracterizacion, Tipoidentificacion, Estados, Ficha
)
# COnvertir ficha de caracterizacion a pdf
from weasyprint import HTML, CSS
# Sirve para Generar tokens, contraseñas y urls
import secrets
# Convertir todo a cadena
import string
import os 
# Poder buscar la ruta para descargar el PDF
from django.conf import settings
# Importar las fechas
import datetime
# Libreria para usar el calendario
import calendar
# Crear copias
import shutil
# Importar mensajes
from django.contrib import messages
# Create your views here.

# =====================================================================
# Consultas dependiendo del rol
# =====================================================================
def consultas_instructor(request):

    # Codigo encargado de generar numeros y letras aleatorios (Link)
    caracteres = string.ascii_letters + string.digits
    codigo = ''.join(secrets.choice(caracteres) for _ in range(5))

    # Traer la sesión del id que se encuantra en el sistema
    user_id = request.session.get('user_id')

    # Obtener el usuario y su rol
    usuario = Usuario.objects.select_related('rol').get(idusuario=user_id)
    id_rol = usuario.rol.idrol

    # Definir layout según rol
    if id_rol == 1:
        layout = 'layout/layoutinstructor.html'
        rol_name = 'Instructor'
    elif id_rol == 2:
        layout = 'layout/layout_coordinador.html'
        rol_name = 'Coordinador'
    elif id_rol == 3:
        layout = 'layout/layout_funcionario.html'
        rol_name = 'Funcionario'
    elif id_rol == 4:
        layout = 'layout/layout_admin.html'
        rol_name = "Administrador"

    """
    ======================================
    Obtener la solicitud para la consulta
    ======================================
    """
    # Solo si el rol es funcionario hará esto
    if id_rol == 3:

        # Fecha actual y rango del mes
        hoy = datetime.date.today()
        anio = hoy.year
        mes = hoy.month
        primer_dia = datetime.date(anio, mes, 1)
        ultimo_dia = datetime.date(anio, mes, calendar.monthrange(anio, mes)[1])

        # Traer todas las solicitudes dentro del mes actual (sin limitar al funcionario logueado)
        solicitudes_mes = Solicitud.objects.select_related('idtiposolicitud').filter(
            fechasolicitud__range=(primer_dia, ultimo_dia)
        ).order_by('-fechasolicitud')  # Ordenar de más reciente a más antigua

        # Filtrar solo las solicitudes que cumplan la condición de cupo
        solicitudes_filtradas = []
        for solicitud in solicitudes_mes:
            aspirantes_registrados = Aspirantes.objects.filter(solicitudinscripcion=solicitud).count()
            if aspirantes_registrados >= solicitud.cupo:
                solicitudes_filtradas.append(solicitud)

        solicitudes = solicitudes_filtradas if solicitudes_filtradas else Solicitud.objects.none()

    else:
        # Para otros roles, traer solo solicitudes del usuario directamente
        solicitudes = Solicitud.objects.select_related('idusuario', 'idtiposolicitud') \
            .filter(idusuario=user_id) \
            .order_by('-fechasolicitud')  # Ordenar de más reciente a más antigua

    # Obtener estados
    estado = Estados.objects.values('idestado', 'estados')

    # Obtener todas las fichas del usuario logueado
    fichas_usuario = Ficha.objects.filter(idusuario=user_id).select_related('idestado', 'idsolicitud')

    # Asignar estado y observación a cada solicitud
    for solicitud in solicitudes:
        # Buscar la ficha relacionada con esta solicitud para el usuario
        ficha = fichas_usuario.filter(idsolicitud=solicitud.idsolicitud).first()
        if ficha:
            solicitud.estado_usuario = ficha.idestado.estados  # Estado de la ficha
            solicitud.observacion_usuario = ficha.observacion  # Observación asociada
        else:
            solicitud.estado_usuario = None
            solicitud.observacion_usuario = None

    # Para roles de instructor (1) y administrador (4), obtener aspirantes de cada solicitud
    if id_rol in [1, 4]:
        for solicitud in solicitudes:
            aspirantes = Aspirantes.objects.select_related(
                'tipoidentificacion', 'idcaracterizacion'
            ).filter(solicitudinscripcion=solicitud.idsolicitud)
            solicitud.aspirantes = aspirantes

    # Renderizar el template
    return render(request, "consultas/consultas_instructor.html", {
        "layout": layout,
        "rol": id_rol,
        "user": rol_name,
        'codigo': codigo,
        'solicitudes': solicitudes,
        'estado': estado,
    })

# ===============================================================================
# Mostrar la ficha de caracterización
# ===============================================================================
def ficha_caracterizacion(request, solicitud_id):
    """
    Vista para mostrar la ficha de caracterización
    """
    # Obtener el usuario actual desde la sesión
    user_id = request.session.get('user_id')
    usuario_actual = get_object_or_404(Usuario.objects.select_related('rol'), idusuario=user_id)
    
    # Obtener la solicitud con todas las relaciones necesarias
    # 🔹 select_related solo con ForeignKey / OneToOne
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'codigoprograma',
            'idhorario', 
            'idmodalidad',
            'codigomunicipio__codigodepartamento',
            'idusuario',
            'idempresa',
            'idespecial',
        ),
        idsolicitud=solicitud_id
    )
    
    # Obtener todas las variables que necesita el template
    programa = solicitud.codigoprograma
    horario = solicitud.idhorario
    modalidad = solicitud.idmodalidad
    municipio = solicitud.codigomunicipio
    departamento = municipio.codigodepartamento
    usuario = solicitud.idusuario
    empresa = solicitud.idempresa
    programa_especial = solicitud.idespecial
    ambiente = solicitud.ambiente  # ✅ Campo de texto, se usa directo
    
    # Definir layout según rol del usuario actual
    id_rol = usuario_actual.rol.idrol
    if id_rol == 1:
        layout = 'layout/layoutinstructor.html'
    elif id_rol == 2:
        layout = 'layout/layout_coordinador.html'
    elif id_rol == 3:
        layout = 'layout/layout_funcionario.html'
    elif id_rol == 4:
        layout = 'layout/layout_admin.html'
    else:
        layout = 'layout/layout_admin.html'
    
    # Contexto que se envía al template
    context = {
        'layout': layout,
        'rol': id_rol,
        'solicitud': solicitud,
        'programa': programa,
        'horario': horario,
        'modalidad': modalidad,
        'departamento': departamento,
        'municipio': municipio,
        'usuario': usuario,
        'empresa': empresa,
        'programa_especial': programa_especial,
        'ambiente': ambiente,  # Se pasa al template como texto
    }
    
    # Renderizar template con datos
    return render(request, 'fichacaracterizacion/fichacaracterizacion.html', context)

# ======================================================================
# Generar la ficha de caracterización en pdf
# ======================================================================

def ficha_caracterizacion_pdf(request, solicitud_id):
    """Genera un PDF de la ficha de caracterización usando WeasyPrint.
    Solo lo guarda en disco si el rol es 3 (funcionario). En otros roles, solo lo descarga sin guardar.
    """

    # Reutilizar la lógica de la vista HTML
    user_id = request.session.get('user_id')
    usuario_actual = get_object_or_404(
        Usuario.objects.select_related('rol'),
        idusuario=user_id
    )

    # 🔹 Quitar 'ambiente' porque es CharField (no relacional)
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'codigoprograma',
            'idhorario',
            'idmodalidad',
            'codigomunicipio__codigodepartamento',
            'idusuario',
            'idempresa',
            'idespecial',
        ),
        idsolicitud=solicitud_id
    )

    # Obtener variables necesarias para el template
    programa = solicitud.codigoprograma
    horario = solicitud.idhorario
    modalidad = solicitud.idmodalidad
    municipio = solicitud.codigomunicipio
    departamento = municipio.codigodepartamento
    usuario = solicitud.idusuario
    empresa = solicitud.idempresa
    programa_especial = solicitud.idespecial
    ambiente = solicitud.ambiente  # ✅ Se accede directo porque es CharField

    # Definir layout según rol
    id_rol = usuario_actual.rol.idrol
    if id_rol == 1:
        layout = 'layout/layoutinstructor.html'
    elif id_rol == 2:
        layout = 'layout/layout_coordinador.html'
    elif id_rol == 3:
        layout = 'layout/layoutfuncionario.html'
    elif id_rol == 4:
        layout = 'layout/layout_admin.html'
    else:
        layout = 'layout/layout_admin.html'

    # Contexto enviado al template
    context = {
        'layout': layout,
        'rol': id_rol,
        'solicitud': solicitud,
        'programa': programa,
        'horario': horario,
        'modalidad': modalidad,
        'departamento': departamento,
        'municipio': municipio,
        'usuario': usuario,
        'empresa': empresa,
        'programa_especial': programa_especial,
        'ambiente': ambiente,  # Se pasa como texto
        'pdf_mode': True,
    }

    # Renderizar HTML con contexto
    html_string = render_to_string('fichacaracterizacion/fichacaracterizacion.html', context)

    # Ruta al CSS
    css_path = os.path.join(settings.BASE_DIR, 'Cursos', 'static', 'css', 'ficha-caracterizacion.css')

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    css = CSS(filename=css_path)

    pdf_bytes = html.write_pdf(stylesheets=[css])

    # ✅ SOLO si el rol es 3, guardar en disco
    if int(id_rol) == 3:
        folder_name = f"solicitud_{solicitud.idsolicitud}"
        carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'funcionario', folder_name)
        os.makedirs(carpeta_destino, exist_ok=True)

        filename_pdf = f"ficha_caracterizacion_{solicitud.idsolicitud}.pdf"
        ruta_guardado = os.path.join(carpeta_destino, filename_pdf)

        # Guardar archivo en disco
        with open(ruta_guardado, 'wb') as f:
            f.write(pdf_bytes)

        # Abrir el archivo guardado para descargarlo
        response_file = open(ruta_guardado, 'rb')
    else:
        # Para otros roles: no guardar en disco, usar los bytes directamente
        response_file = BytesIO(pdf_bytes)  # 🔹 Usar BytesIO para respuesta directa

    # Descargar el archivo
    return FileResponse(
        response_file,
        as_attachment=True,
        filename='ficha_caracterizacion.pdf',
        content_type='application/pdf'
    )

# ========================================================================
# Descargar el PDF combinado de los aspirantes
# ========================================================================

def descargar_pdf(request, id, idrol):
    folder_name = f"solicitud_{id}"

    # Ruta del archivo original
    buscar_pdf = os.path.join(settings.MEDIA_ROOT, 'pdf', folder_name, 'combinado.pdf')

    if not os.path.exists(buscar_pdf):
        raise Http404("PDF no encontrado")

    # Si el rol es 3 = funcionario crear una copia del archivo
    if int(idrol) == 3:
        # Ruta de destino donde se guardará una copia
        carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'Funcionario',  folder_name)
        os.makedirs(carpeta_destino, exist_ok=True)

        guardar_pdf = os.path.join(carpeta_destino, 'combinado.pdf')

        # Copiar el archivo original al nuevo destino
        shutil.copy2(buscar_pdf, guardar_pdf)

    # Descargar el archivo original
    return FileResponse(
        open(buscar_pdf, 'rb'),
        as_attachment=True,
        filename='Documentos_aspirantes.pdf',
        content_type='application/pdf'
    )

# =======================================================================
# Descargar excel como funcionario
# =======================================================================

def descargar_excel(request, id, idrol):
    folder_name = f"solicitud_{id}"

    buscar_excel = os.path.join(settings.MEDIA_ROOT, 'excel', f'formato_inscripcion_{id}.xlsx')

    if not os.path.exists(buscar_excel):
        raise Http404("Excel no encontrado")

    # Si el rol es 3 = funcionario crear una copia del archivo
    if int(idrol) == 3:
        # Ruta de destino donde se guardará una copia
        carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'Funcionario', folder_name)
        os.makedirs(carpeta_destino, exist_ok=True)

        guardar_excel = os.path.join(carpeta_destino, f'formato_inscripcion_{id}.xlsx')

        # Copiar el archivo original al nuevo destino
        shutil.copy2(buscar_excel, guardar_excel)

    # Descargar el archivo original
    return FileResponse(
        open(buscar_excel, 'rb'),
        as_attachment=True,
        filename='Formato_inscripcion.xlsx',
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ========================================================================
# Descargar la carta de solicitud de la empresa
# ========================================================================

def descargar_carta(request, id, idrol): 
    # Buscar la solicitud
    buscar_nit = Solicitud.objects.get(idsolicitud=id)

    # Obtener NIT de la empresa relacionada
    nit = buscar_nit.idempresa.nitempresa

    guardar_carta = f"solicitud_{id}"

    # Nombre de la carpeta
    folder_name = f"carta_{nit}"

    # Ruta del archivo original (en su carpeta correspondiente)
    buscar_carta = os.path.join(settings.MEDIA_ROOT, 'Cartas_de_solicitud', folder_name, f'carta_{nit}.pdf')

    if not os.path.exists(buscar_carta):
        raise Http404("PDF no encontrado")

    # Si el rol es 3 = funcionario, crear una copia del archivo
    if int(idrol) == 3:
        # Carpeta destino
        carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'Funcionario', guardar_carta)
        os.makedirs(carpeta_destino, exist_ok=True)

        # Ruta completa del archivo copia
        generar_copia = os.path.join(carpeta_destino, f'carta_{nit}.pdf')

        # Copiar el archivo original al nuevo destino
        shutil.copy2(buscar_carta, generar_copia)

    # Descargar el archivo original
    return FileResponse(
        open(buscar_carta, 'rb'),
        as_attachment=True,
        filename='Carta solicitud.pdf',
        content_type='application/pdf'
    )

# ===========================================
# Funcionario respuestas a las solicitudes
# ===========================================

def revision_fichas(request, id):

    # Buscar la solicitud
    solicitud = get_object_or_404(Solicitud, idsolicitud=id)

    # Obtener el id del usuario en sesión
    user_id = request.session.get('user_id')

    # Obtener el usuario y su rol
    usuario = Usuario.objects.select_related('rol').get(idusuario=user_id)
    id_rol = usuario.rol.idrol

    # Definir layout según rol del usuario actual
    if id_rol == 1:
        layout = 'layout/layoutinstructor.html'
    elif id_rol == 2:
        layout = 'layout/layout_coordinador.html'
    elif id_rol == 3:
        layout = 'layout/layout_funcionario.html'
    elif id_rol == 4:
        layout = 'layout/layout_admin.html'
    else:
        layout = 'layout/layout_admin.html'

    # Validar envío de formulario
    if request.method == "POST":
        try:
            # Capturar datos enviados
            estados = request.POST.get('estado')
            numero_ficha = request.POST.get('codigo_ficha')
            observacion = request.POST.get('observacion')
            nuevo_archivo = request.FILES.get('actualizar_excel')

            # Crear carpeta donde se van a almacenar los formatos
            carpeta_almacenar = f"solicitud_{id}"
            excel_archivo = f"formato_inscripcion_{id}.xlsx"
            carpeta_excel = os.path.join(settings.MEDIA_ROOT, 'Funcionario', carpeta_almacenar, 'Masivos_sofia_plus')
            os.makedirs(carpeta_excel, exist_ok=True)

            # Ruta completa
            directorio_excel = os.path.join(carpeta_excel, excel_archivo)

            # Guardar el archivo físicamente
            if nuevo_archivo:
                with open(directorio_excel, 'wb+') as destino:
                    for chunk in nuevo_archivo.chunks():
                        destino.write(chunk)

            # Validar duplicados correctamente y con redirect al mismo formulario
            duplicado = Ficha.objects.filter(
                codigoficha=numero_ficha
            ).exists()

            if duplicado:
                messages.error(request, 'La ficha ya existe')
                return redirect('consultas_instructor')

            # Obtener objetos relacionados
            id_estado = Estados.objects.get(idestado=estados)

            # Ya tienes la solicitud desde arriba, no es necesario volver a consultarla
            usuario_solicitud = solicitud
            creado_por = usuario_solicitud.idusuario

            # Crear registro en la tabla de aspirantes
            Ficha.objects.create(
                codigoficha=numero_ficha,
                idsolicitud=solicitud,
                idestado=id_estado,
                idusuario=creado_por,
                observacion=observacion,
            )

            # Mensaje de éxito
            messages.success(request, 'Haz enviado respuesta a esta solicitud')
            return redirect('consultas_instructor')

        except Exception as e:
            # Mensaje de error en caso de excepción
            messages.error(request, f'Error al enviar respuesta: {e}')
            return redirect('consultas_instructor')

    # Renderizar plantilla si no hay envío de formulario
    return render(request, 'consultas/consultas_instructor.html', {
        'layout': layout,
        'messages': messages
    })

# ===============================================================
# Descargar el formato generado por sofia plus
# ===============================================================

def descargar_excel_ficha(request, id):
    # Nombre del archivo esperado
    excel_archivo = f"formato_inscripcion_{id}.xlsx"
    
    # Ruta completa donde debe estar almacenado el archivo
    carpeta_excel = os.path.join(settings.MEDIA_ROOT, 'Funcionario', f"solicitud_{id}", 'Masivos_sofia_plus')
    directorio_excel = os.path.join(carpeta_excel, excel_archivo)

    # Validar si el archivo existe antes de descargar
    if os.path.exists(directorio_excel):
        with open(directorio_excel, 'rb') as archivo:
            response = HttpResponse(
                archivo.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response['Content-Disposition'] = f'attachment; filename={excel_archivo}'
            return response
    else:
        # Si no existe, mostrar un error
        raise Http404("Aun no se ha subido el excel.")
