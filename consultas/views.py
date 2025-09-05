from django.shortcuts import render, get_object_or_404
from Cursos.models import (
    Usuario, Solicitud, Programaformacion, Horario, Modalidad, 
    Departamentos, Municipios, Empresa, Programaespecial, Ambiente
)
# Sirve para Generar tokens, contraseñas y urls
import secrets
# Convertir todo a cadena
import string

# Create your views here.

def consultas_instructor(request):


    # Codigo encargado de generar numeros y letras aleatorios con las importaciones
    caracteres = string.ascii_letters + string.digits
    # choice = Elegir elemento al azar 
    # Join = Concatencaión de caracteres
    codigo = ''.join(secrets.choice(caracteres) for _ in range(5))

    user_id = request.session.get('user_id')

    # Obtener el rol por medio del id del usuario que ingreso
    usuario = Usuario.objects.select_related('rol').get(idusuario=user_id)

    # Crear una variable para almacenar el rol
    id_rol = usuario.rol.idrol

    # Definir layout según rol
    if id_rol == 1:
        layout = 'layout/layoutinstructor.html'
        rol_name = 'Instructor'
    elif id_rol == 2:
        layout = 'layout/layoutcoordinador.html'
        rol_name = 'Coordinador'
    elif id_rol == 3:
        layout = 'layout/layoutfuncionario.html'
        rol_name = 'Funcionario'
    elif id_rol == 4:
        layout = 'layout/layout_admin.html'
        rol_name = "Administrador"

    
    """
    ======================================
    Obtener la solicitud para la consulta
    ======================================
    """

    solicitudes = Solicitud.objects.select_related(
        'idusuario'   
        ).filter(idusuario=user_id)

    # programa_formacion = Solicitud.objects.select_related('codigoprograma')

    return render(request, "consultas/consultas_instructor.html", {
            "layout": layout,
            "rol": id_rol,
            "user": rol_name,
            'codigo': codigo,
            'solicitudes': solicitudes,
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
        layout = 'layout/layoutcoordinador.html'
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
    }
    
    return render(request, 'fichacaracterizacion/fichacaracterizacion.html', context)