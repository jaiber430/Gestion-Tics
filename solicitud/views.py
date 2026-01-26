from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
# Se usa para obtener la fecha y horas del país
from django.utils import timezone
# Juntar datos que deben completarse para la Db (transaction) y trabajar con los campos de los modelos (models)
from django.db import transaction
# Importar fechas
from datetime import datetime
import json
# Importar datos de los modulos requeridos
from Cursos.models import (Area, Departamentos,
                            Empresa, Horario, Modalidad, Municipios,Programaespecial,
                            Programaformacion, Solicitud, Tipoempresa, Tipoidentificacion,
                            Tiposolicitud, Usuario)

# Requerido para crear carpetas en rutas especificas
import os
from django.conf import settings

# Importar decorador personalizado
from Cursos.views import login_required_custom

# ===============================
# Función auxiliar para obtener datos comunes
# ===============================
def _get_common_context():
    """
    Devuelve un diccionario con todos los objetos de DB necesarios para el formulario.
    """
    return {
        'areas': Area.objects.all(),
        'empresas': Empresa.objects.all(),
        'departamentos': Departamentos.objects.all(),
        'tipos_empresas': Tipoempresa.objects.all(),
        'modalidades': Modalidad.objects.all(),
        'municipios': Municipios.objects.all(),
        'programas_especiales': Programaespecial.objects.all(),
        'programas_formacion': Programaformacion.objects.select_related('idarea').all(),
    }


# ===============================
# Vista: Crear Solicitud
# ===============================
@login_required_custom
def crear_solicitud(request):
    """
    Página para decidir qué ficha crear: regular o campesina
    """
    # Llamar el id del usuario
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect('login')

    try:
        usuario = Usuario.objects.select_related('rol').get(idusuario=user_id)
        id_rol = usuario.rol.idrol

        # Definir layout según el rol
        if id_rol == 1:
            layout = 'layout/layoutinstructor.html'
            rol_name = 'Instructor'
        elif id_rol == 2:
            layout = 'layout/layout_coordinador.html'
            rol_name = 'Coordinador'
        elif id_rol == 3:
            layout = 'layout/layoutfuncionario.html'
            rol_name = 'Funcionario'
        elif id_rol == 4:
            layout = 'layout/layout_admin.html'
            rol_name = "Administrador"

        # Verificar fecha
        hoy = datetime.now().day
        if (hoy in range (1,16)):
            dato = 'Creaciones_abiertas'
        else:
            dato= 'Creaciones_cerradas'

    except Usuario.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect('login')

    # Llamar contexto común
    context = _get_common_context()
    context.update({'layout': layout, 'user': rol_name, 'rol': id_rol, 'fechas': dato})
    return render(request, 'pages/creacion.html', context)


# ===============================
# Función base para crear solicitudes
# ===============================
@login_required_custom
def _crear_solicitud_base(request, tipo_solicitud_id, template_name, mensaje_exito):
    """
    Función base para crear solicitudes (regular o campesina)
    """

    # Verificar usuario en sesión
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Debes iniciar sesión para acceder.")
        return redirect('login')

    try:
        usuario = Usuario.objects.select_related('rol').get(idusuario=user_id)
        id_rol = usuario.rol.idrol

        # Definir layout según el rol
        if id_rol == 1:
            layout = 'layout/layoutinstructor.html'
            rol_name = 'Instructor'
        elif id_rol == 2:
            layout = 'layout/layout_coordinador.html'
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

    # Llamar contexto común
    context = _get_common_context()
    context.update({'layout': layout, 'user': rol_name, 'rol': id_rol})

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # ===============================
                # Datos principales recibidos del formulario
                # ===============================
                tiene_empresa = request.POST.get('tieneEmpresa')
                nombre_programa_codigo = request.POST.get('nombrePrograma_codigo')
                version_programa = request.POST.get('versionPrograma')
                subsector_economico = request.POST.get('subsectorEconomico')
                fecha_inicio = request.POST.get('fechaInicio')
                fecha_finalizacion = request.POST.get('fechaFinalizacion')
                cupo_aprendices = request.POST.get('cupoAprendices')
                municipio_formacion = request.POST.get('municipioFormacion')
                direccion_formacion = request.POST.get('direccionFormacion')
                dias_semana = request.POST.getlist('diasSemana[]')
                hora_inicio = request.POST.get('horario_inicio') or request.POST.get('horarioInicio')
                hora_fin = request.POST.get('horario_fin') or request.POST.get('horarioFin')
                fechas_calendario_raw = request.POST.get('fechas_calendario')

                try:
                    fechas_calendario = json.loads(fechas_calendario_raw) if fechas_calendario_raw else []
                except json.JSONDecodeError:
                    fechas_calendario = []

                # ===============================
                # Campos de empresa
                # ===============================
                empresa_solicitante = request.POST.get('empresaSolicitante', '')
                tipo_empresa = request.POST.get('tipoEmpresa', '')
                nombre_responsable = request.POST.get('nombreResponsable', '')
                correo_responsable = request.POST.get('correoResponsable', '')
                nit_empresa = request.POST.get('nitEmpresa', '')
                carta_solicitud = request.FILES.get('cartaSolicitud', '')

                # ===============================
                # Campos opcionales
                # ===============================
                programa_especial = request.POST.get('programaEspecial')
                convenio = request.POST.get('convenio', '')
                nombre_ambiente = request.POST.get('nombreAmbiente')

                if fechas_calendario:
                    fechas_ordenadas = sorted(fechas_calendario)
                    dias = [f.split('-')[2] if '-' in f else f for f in fechas_ordenadas]
                    mitad = len(dias) // 2
                    if mitad > 0:
                        mes1_fechas = ', '.join(dias[:mitad])
                        if len(dias) > mitad:
                            mes2_fechas = ', '.join(dias[mitad:])
                    else:
                        mes1_fechas = ', '.join(dias)
                else:
                    mes1_fechas, mes2_fechas = None, None

                # ===============================
                # Validación: evitar duplicados de ambiente + fechas + horas + días
                # ===============================
                if Solicitud.objects.filter(
                    ambiente=nombre_ambiente,
                    idhorario__fechainicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
                    idhorario__fechafin=datetime.strptime(fecha_finalizacion, '%Y-%m-%d').date(),
                    idhorario__horas=f"{hora_inicio}-{hora_fin}",
                    idhorario__diassemana=', '.join(dias_semana)
                ).exists():
                    messages.error(
                        request,
                        "Ya existe una solicitud con este ambiente, fechas y horario."
                    )
                    return redirect('Crearsolicitud')

                # ===============================
                # Crear horario
                # ===============================
                horario = Horario.objects.create(
                    fechainicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
                    fechafin=datetime.strptime(fecha_finalizacion, '%Y-%m-%d').date(),
                    mes1=mes1_fechas if mes1_fechas else None,
                    mes2=mes2_fechas if mes2_fechas else None,
                    horas=f"{hora_inicio}-{hora_fin}",
                    diassemana=', '.join(dias_semana)
                )

                # ===============================
                # Empresa opcional
                # ===============================
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

                # ===============================
                # Crear la solicitud
                # ===============================
                programa_formacion = Programaformacion.objects.get(codigoprograma=nombre_programa_codigo)
                modalidad = Modalidad.objects.get(idmodalidad=1)
                municipio = Municipios.objects.get(codigomunicipio=municipio_formacion)
                programa_especial_obj = Programaespecial.objects.get(idespecial=programa_especial)
                tipo_solicitud = Tiposolicitud.objects.get(idtiposolicitud=tipo_solicitud_id)

                solicitud_creada = Solicitud.objects.create(
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
                    ambiente=nombre_ambiente,
                    fechasolicitud=timezone.now().date(),
                    revisado=0,
                    linkpreinscripcion=0
                )

                # ===============================
                # Guardar carta en carpeta específica (solo si la solicitud se creó)
                # ===============================
                if carta_solicitud:
                    # Carpeta basada en el ID de la solicitud recién creada
                    folder_name = f"carta_{solicitud_creada.idsolicitud}"
                    carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'Cartas_de_solicitud', folder_name)
                    os.makedirs(carpeta_destino, exist_ok=True)

                    filename_pdf = f"carta_{solicitud_creada.idsolicitud}.pdf"
                    ruta_guardado = os.path.join(carpeta_destino, filename_pdf)

                    # Guardar archivo en disco
                    with open(ruta_guardado, 'wb') as f:
                        for chunk in carta_solicitud.chunks():
                            f.write(chunk)


                # Mensaje de éxito
                messages.success(request, mensaje_exito)
                return redirect('Crearsolicitud')

        except Exception as e:
            messages.error(request, f'Error al crear la solicitud: {str(e)}')
            return redirect('Crearsolicitud')

    return render(request, template_name, context)


# ===============================
# Vista: Solicitud Regular
# ===============================
@login_required_custom
def solicitud_regular(request):
    return _crear_solicitud_base(
        request,
        tipo_solicitud_id=1,
        template_name='forms/crearsolicitudregular.html',
        mensaje_exito='Solicitud de ficha regular creada exitosamente.'
    )


# ===============================
# Vista: Solicitud Campesina
# ===============================
@login_required_custom
def solicitud_campesina(request):
    return _crear_solicitud_base(
        request,
        tipo_solicitud_id=2,
        template_name='forms/crearsolicitudcampesina.html',
        mensaje_exito='Solicitud de ficha campesina creada exitosamente.'
    )
