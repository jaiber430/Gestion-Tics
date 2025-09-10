from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from Cursos.models import (
    Usuario, Solicitud, Programaformacion, Horario, Modalidad, 
    Departamentos, Municipios, Empresa, Programaespecial, Ambiente,
    Aspirantes, Caracterizacion, Tipoidentificacion, Estados
)
from django.conf import settings
import os
from weasyprint import HTML, CSS
# Sirve para Generar tokens, contraseñas y urls
import secrets
# Convertir todo a cadena
import string
import os 
from django.http import Http404, FileResponse,  HttpResponse

# Poder buscar la ruta para descargar el PDF
from django.conf import settings

# Libreria de Django para generar un excel
from openpyxl import Workbook
# Importar las fechas
import datetime
# Libreria para usar el calendario
import calendar
# Crear copias
import shutil
# Create your views here.

def consultas_instructor(request):

    # Codigo encargado de generar numeros y letras aleatorios
    caracteres = string.ascii_letters + string.digits
    codigo = ''.join(secrets.choice(caracteres) for _ in range(5))

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
    if id_rol == 3:

        # Fecha actual y rango del mes
        hoy = datetime.date.today()
        anio = hoy.year
        mes = hoy.month
        primer_dia = datetime.date(anio, mes, 1)
        ultimo_dia = datetime.date(anio, mes, calendar.monthrange(anio, mes)[1])

        # Traer todas las solicitudes dentro del mes actual (sin limitar al funcionario logueado)
        solicitudes_mes = Solicitud.objects.filter(
            fechasolicitud__range=(primer_dia, ultimo_dia)
        )

        # Filtrar solo las solicitudes que cumplan la condición de cupo
        solicitudes_filtradas = []
        for solicitud in solicitudes_mes:
            aspirantes_registrados = Aspirantes.objects.filter(solicitudinscripcion=solicitud).count()
            if aspirantes_registrados >= solicitud.cupo:
                solicitudes_filtradas.append(solicitud)

        solicitudes = solicitudes_filtradas if solicitudes_filtradas else Solicitud.objects.none()

    else:
        # Para otros roles, traer solicitudes del usuario directamente
        solicitudes = Solicitud.objects.select_related('idusuario').filter(idusuario=user_id)

    # Obtener estados
    estado = Estados.objects.values('idestado', 'estados')

    # Para roles de instructor (1) y administrador (4), obtener aspirantes de cada solicitud
    solicitudes_con_aspirantes = []
    if id_rol in [1, 4]:  # Solo para instructor y administrador
        for solicitud in solicitudes:
            # Obtener aspirantes relacionados con esta solicitud con toda la información necesaria
            aspirantes = Aspirantes.objects.select_related(
                'tipoidentificacion', 'idcaracterizacion'
            ).filter(solicitudinscripcion=solicitud.idsolicitud)
            
            # Agregar los aspirantes a la solicitud como un atributo temporal
            solicitud.aspirantes = aspirantes
            solicitudes_con_aspirantes.append(solicitud)
        solicitudes = solicitudes_con_aspirantes

    # Renderizar el template
    return render(request, "consultas/consultas_instructor.html", {
        "layout": layout,
        "rol": id_rol,
        "user": rol_name,
        'codigo': codigo,
        'solicitudes': solicitudes,
        'estado': estado,
    })


def ficha_caracterizacion(request, solicitud_id):
    """
    Vista para mostrar la ficha de caracterización
    """
    user_id = request.session.get('user_id')
    usuario_actual = get_object_or_404(Usuario.objects.select_related('rol'), idusuario=user_id)
    
    # Obtener la solicitud con todas las relaciones necesarias
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'codigoprograma',
            'idhorario', 
            'idmodalidad',
            'codigomunicipio__codigodepartamento',
            'idusuario',
            'idempresa',
            'idespecial',
            'ambiente'
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
    ambiente = solicitud.ambiente
    
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
        'ambiente': ambiente,
    }
    
    return render(request, 'fichacaracterizacion/fichacaracterizacion.html', context)

def ficha_caracterizacion_pdf(request, solicitud_id):
    """Genera un PDF de la ficha de caracterización usando WeasyPrint.
    Solo lo guarda en disco si el rol es 3 (funcionario). En otros roles, solo lo descarga sin guardar.
    """

    # Reutilizar la lógica de la vista HTML
    user_id = request.session.get('user_id')
    usuario_actual = get_object_or_404(Usuario.objects.select_related('rol'), idusuario=user_id)
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'codigoprograma', 'idhorario', 'idmodalidad', 'codigomunicipio__codigodepartamento',
            'idusuario', 'idempresa', 'idespecial', 'ambiente'
        ), idsolicitud=solicitud_id
    )
    programa = solicitud.codigoprograma
    horario = solicitud.idhorario
    modalidad = solicitud.idmodalidad
    municipio = solicitud.codigomunicipio
    departamento = municipio.codigodepartamento
    usuario = solicitud.idusuario
    empresa = solicitud.idempresa
    programa_especial = solicitud.idespecial
    ambiente = solicitud.ambiente

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
        'ambiente': ambiente,
        'pdf_mode': True,
    }

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

        # Guardar el archivo en disco
        with open(ruta_guardado, 'wb') as f:
            f.write(pdf_bytes)

        # Abrir el archivo guardado para descargarlo
        response_file = open(ruta_guardado, 'rb')
    else:
        # Para otros roles: no guardar en disco, usar los bytes directamente
        response_file = pdf_bytes

    # Descargar el archivo (desde disco si rol=3, desde bytes si otro rol)
    return FileResponse(
        response_file,
        as_attachment=True,
        filename='Documentos_aspirantes.pdf',
        content_type='application/pdf'
    )

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

def generar_excel(request, idsolicitud):
    # Asegurarse de que el id este siendo enviado cuando se oprima el boton de descargar
    solicitud = get_object_or_404(Solicitud, idsolicitud=idsolicitud)

    # Consulta para obtener el nombre del programa relacionado con la solicitud 
    programa = solicitud.codigoprograma  # Ya tienes la solicitud, accedes directo al FK
    # Mostrar el nombre del programa
    nombre_programa = programa.nombreprograma
 
    # Crear un nuevo archivo de excel en blanco
    nuevo_archivo = Workbook()
    # Selceccionar la hoja del excel (Primera por defecto)
    hoja = nuevo_archivo.active
    # Colocar nombre a esa hoja 
    hoja.title = f"Aspirantes Inscritos"

    # Agregar fila a la hoja de excel con los siguientes encabezados
    hoja.append(['Tipo de identificacion', 'Numero identificacion', 'Codigo de ficha', 'Tipo poblacion aspirantes', 'Codigo empresa'])

    # Consulta para obtener los aspirantes relacionados con la solicitud 
    aspirantes = Aspirantes.objects.filter(solicitudinscripcion=solicitud)

    for agregar in aspirantes:
        # Nombre del tipo de población
        caracterizacion = agregar.idcaracterizacion
        tipo_caracterizacion = caracterizacion.caracterizacion

        # Nombre del tipo de identificacion
        identificacion = agregar.tipoidentificacion
        tipo_identificacion = identificacion.tipoidentificacion

        # Buscar el NIT de la empresa desde la solicitud
        empresa = agregar.solicitudinscripcion.idempresa
        if empresa is not None:
            mostrar_empresa = empresa.nitempresa
        else:
            mostrar_empresa = ''

        hoja.append([
            tipo_identificacion, 
            agregar.numeroidentificacion, 
            '',  # Código de ficha (no definido aún)
            tipo_caracterizacion, 
            mostrar_empresa
        ])

    # Crear carpeta donde se van a almacenar los formatos masivos
    nombre_archivo_excel = f"formato_inscripcion_{idsolicitud}.xlsx"
    carpeta_excel = os.path.join(settings.MEDIA_ROOT, 'excel')
    os.makedirs(carpeta_excel, exist_ok=True)

    # Direción donde se encuntra el directorio
    directorio_excel = os.path.join(carpeta_excel, nombre_archivo_excel)

    # Guardar directorio
    nuevo_archivo.save(directorio_excel)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Formato inscripcion masivo.xlsx'

    nuevo_archivo.save(response)
    return response

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
