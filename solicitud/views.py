from django.shortcuts import render, redirect
from django.contrib import messages
# Se usa para obtener la fecha y horas del país
from django.utils import timezone
# Juntar datos que deben completarse para la Db (transaction) y trabajar con los campos de los modelos (models)
from django.db import transaction, models
# Importar fehas 
from datetime import datetime
# Importar datos de los modulos requeridos
from Cursos.models import (
    Ambiente, Area, Departamentos, Empresa, Horario, Modalidad, Municipios,
    Programaespecial, Programaformacion, Solicitud, Tipoempresa, Tiposolicitud, Usuario
)

def _get_common_context():
    """
    Devuelve un diccionario con todos los objetos de DB necesarios para el formulario.
    """
    return {
        'ambientes': Ambiente.objects.all(),
        'areas': Area.objects.all(),
        'empresas': Empresa.objects.all(),
        'departamentos': Departamentos.objects.all(),
        'tipos_empresas': Tipoempresa.objects.all(),
        'modalidades': Modalidad.objects.all(),
        'municipios': Municipios.objects.all(),
        'programas_especiales': Programaespecial.objects.all(),
        'programas_formacion': Programaformacion.objects.select_related('idarea').all(),
    }

def crear_solicitud(request):
    """
    Página para decidir qué ficha crear: regular o campesina
    """
    # Llamar el id del usuario 
    user_id = request.session.get('user_id')
    # Se asegura de que el ID del usuario esxista
    if not user_id:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect('login')

    try:
        # Ontener el rol por medio del id del usuario que ingreso
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

        # Verificar fecha para crear cursos
        hoy = datetime.now().day
        # Verificar fecha para crear cursos
        hoy = datetime.now().day
        if (hoy in range (1,16)):
            dato = 'Creaciones_abiertas'
        else:
            dato= 'Creaciones_cerradas'

    except Usuario.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect('login')

    context = _get_common_context()
    context.update({'layout': layout, 'user': rol_name, 'rol': id_rol, 'fechas': dato})
    return render(request, 'pages/creacion.html', context)


def solicitud_regular(request):
    """
    Crear la solicitud regular
    """
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect('login')

    try:
        usuario = Usuario.objects.select_related('rol').get(idusuario=user_id)
        id_rol = usuario.rol.idrol

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

    except Usuario.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect('login')

    context = _get_common_context()
    context.update({'layout': layout, 'user': rol_name, 'rol': id_rol})

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos principales
                tiene_empresa = request.POST.get('tieneEmpresa')
                # tipo_modalidad = request.POST.get('tipoModalidad')
                nombre_programa_codigo = request.POST.get('nombrePrograma_codigo')
                version_programa = request.POST.get('versionPrograma')
                subsector_economico = request.POST.get('subsectorEconomico')
                fecha_inicio = request.POST.get('fechaInicio')
                fecha_finalizacion = request.POST.get('fechaFinalizacion')
                cupo_aprendices = request.POST.get('cupoAprendices')
                municipio_formacion = request.POST.get('municipioFormacion')
                direccion_formacion = request.POST.get('direccionFormacion')
                dias_semana = request.POST.getlist('diasSemana[]')
                horario_curso = request.POST.get('horarioCurso')
                fechas_ejecucion_mes1 = request.POST.get('fechasEjecucionMes1')
                fechas_ejecucion_mes2 = request.POST.get('fechasEjecucionMes2', '')

                # Campos de empresa
                empresa_solicitante = request.POST.get('empresaSolicitante', '')
                tipo_empresa = request.POST.get('tipoEmpresa', '')
                nombre_responsable = request.POST.get('nombreResponsable', '')
                correo_responsable = request.POST.get('correoResponsable', '')
                nit_empresa = request.POST.get('nitEmpresa', '')

                # Campos opcionales
                programa_especial = request.POST.get('programaEspecial')
                convenio = request.POST.get('convenio', '')
                nombre_ambiente = request.POST.get('nombreAmbiente')

                # Crear horario
                horario = Horario.objects.create(
                    fechainicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
                    fechafin=datetime.strptime(fecha_finalizacion, '%Y-%m-%d').date(),
                    mes1=f"{fechas_ejecucion_mes1} - Días: {', '.join(dias_semana)} - Horario: {horario_curso}",
                    mes2=fechas_ejecucion_mes2 or None
                )

                # Empresa opcional
                empresa_obj = None
                if tiene_empresa == 'si':
                    empresa_obj = Empresa.objects.filter(nombreempresa=empresa_solicitante).first()
                    if not empresa_obj:
                        tipo_empresa_obj = Tipoempresa.objects.get(idtipoempresa=tipo_empresa)
                        nit_valor = int(nit_empresa) if nit_empresa.isdigit() else 0
                        empresa_obj = Empresa.objects.create(
                            nombreempresa=empresa_solicitante,
                            representanteempresa=nombre_responsable,
                            correoempresa=correo_responsable,
                            nitempresa=nit_valor,
                            idtipoempresa=tipo_empresa_obj
                        )

                programa_formacion = Programaformacion.objects.get(codigoprograma=nombre_programa_codigo)
                modalidad = Modalidad.objects.get(idmodalidad=1)
                municipio = Municipios.objects.get(codigomunicipio=municipio_formacion)
                programa_especial_obj = Programaespecial.objects.get(idespecial=programa_especial)
                ambiente_obj = Ambiente.objects.filter(idambiente=nombre_ambiente).first() if nombre_ambiente else None
                tipo_solicitud = Tiposolicitud.objects.get(idtiposolicitud=1)

                # Generar código de solicitud
                ultimo_codigo = Solicitud.objects.aggregate(max_codigo=models.Max('codigosolicitud'))['max_codigo']
                nuevo_codigo = (ultimo_codigo or 0) + 1

                Solicitud.objects.create(
                    idtiposolicitud=tipo_solicitud,
                    codigoprograma=programa_formacion,
                    idhorario=horario,
                    cupo=int(cupo_aprendices),
                    idmodalidad=modalidad,
                    codigomunicipio=municipio,
                    direccion=direccion_formacion,
                    idusuario=usuario,
                    idempresa=empresa_obj,
                    subsectoreconomico=subsector_economico,
                    idespecial=programa_especial_obj,
                    convenio=convenio or None,
                    ambiente=ambiente_obj,
                    fechasolicitud=timezone.now().date()
                )

                messages.success(request, 'Solicitud de ficha regular creada exitosamente.')
                return redirect('crearregular')

        except Exception as e:
            messages.error(request, f'Error al crear la solicitud: {str(e)}')

    return render(request, 'forms/crearsolicitudregular.html', context)
