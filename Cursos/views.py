from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Cursos.models import Usuario, Solicitud, Ficha, Estados, EstadosCoordinador, Solicitudcoordinador, Aspirantes, Tipoidentificacion, Rol, Tipocontrato, Usuariosasignados
import string, secrets
import datetime, calendar
from functools import wraps
from django.contrib.auth import logout as django_logout


# ===============================
# Decorador personalizado
# ===============================
def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            messages.error(request, "Debes iniciar sesión primero")
            return redirect("index")  # nombre de tu URL para la página de login
        return view_func(request, *args, **kwargs)
    return wrapper

# ===============================
# Vista de inicio
# ===============================
def index(request):
    return render(request, "inicio/index.html", {
        'Title': 'Hi',
    })

# ===============================
# Vista de login
# ===============================
def login_view(request):
    if request.method == "POST":
        numero_identificacion = request.POST.get("numeroCedula")
        clave = request.POST.get("clave")
        rol = int(request.POST.get("rol"))

        try:
            # Buscar usuario
            user = Usuario.objects.get(
                numeroidentificacion=numero_identificacion,
                clave=clave,
                rol=rol,
                verificado=1
            )

            # Guardar en sesión
            request.session['user_id'] = user.idusuario
            request.session['name'] = user.nombre
            request.session['rol'] = rol

            # Layout y rol_name
            if rol == 1:
                layout = "layout/layoutinstructor.html"
                rol_name = "Instructor"
            elif rol == 2:
                layout = "layout/layout_coordinador.html"
                rol_name = "Coordinador"
            elif rol == 3:
                layout = "layout/layout_funcionario.html"
                rol_name = "Funcionario"
            elif rol == 4:
                layout = "layout/layout_admin.html"
                rol_name = "Administrador"
            elif rol == 5:
                layout = "layout/layout_programa.html"
                rol_name = "Modificador"
            else:
                layout = "layout/layout_desconocido.html"
                rol_name = "Desconocido"

            return render(request, "user/inicio.html", {
                "layout": layout,
                "rol": rol,
                "user": rol_name,
                "id": user.idusuario,
                "name": user.nombre,
            })

        except Usuario.DoesNotExist:
            messages.error(request, 'Su usuario aun no ha sido verificado por un administardor o las credenciales son incorrectas')
            return render(request, "inicio/index.html")

    return render(request, "inicio/index.html")

# ==============================================
# Cerrar sesion
# ==============================================

def cerrar_sesion(request):
    """
    Cierra la sesión del usuario y lo redirige al login
    """

    # Si quieres usar el sistema de auth de Django
    django_logout(request)

    # O limpiar todo lo que hayas guardado en sesión
    request.session.flush()

    # Mensaje de confirmación
    messages.success(request, "Sesión cerrada correctamente.")

    # Redirigir al inicio o al login
    return redirect("login")

@login_required_custom
def verificacion_usuario(request):
    # Trae todos los usuarios con verificado=0
    usuariosSinAprobar = Usuario.objects.filter(verificado=0)
    return render(request, 'inicio/verificarUsuarios.html',{
        'usuariosSinVerificar': usuariosSinAprobar,
    })

@login_required_custom
def verificar_usuario(request, idusuario):
    if request.method == "POST":
        try:
            # 1. Obtener el valor del select "rol"
            rol_id = request.POST.get('rol')

            # 2. Validar que el usuario exista
            usuario = Usuario.objects.get(idusuario=idusuario)

            # 3. Manejar si el rol viene vacío ("" -> None)
            if not rol_id:
                usuario.rol = None
            else:
                usuario.rol_id = int(rol_id)  # Asigna FK correctamente

            # 4. Marcar como verificado
            usuario.verificado = 1
            usuario.save()

            messages.success(request, f'Usuario {usuario.nombre} ha sido verificado correctamente.')

        except Usuario.DoesNotExist:
            messages.error(request, 'El usuario no existe.')

        except Rol.DoesNotExist:
            messages.error(request, 'El rol seleccionado no existe.')

        except Exception as e:
            messages.error(request, f'Error al verificar usuario: {str(e)}')

    return redirect('verificacion_usuario')


def registerUser(request):
    # Si es POST, procesa el registro
    if request.method == 'POST':
        # Obtener datos del usuario
        nombreUser = request.POST.get('nombre')
        apellidoUser = request.POST.get('apellido')
        rolUser = None
        tipoIdentificacionUser = request.POST.get('tipo_documento')
        numeroIdentificacionUser = request.POST.get('numeroCedula')
        correoUser = request.POST.get('correo')
        claveUser = request.POST.get('clave')
        contratoUser = request.POST.get('contrato')
        numeroContrato = request.POST.get('numeroContrato') or None

        fechaRegistroUser = datetime.datetime.now()
        verificacionUser = 0

        # Validar si la cédula ya existe
        if Usuario.objects.filter(numeroidentificacion=numeroIdentificacionUser).exists():
            messages.error(request, 'El número de cédula ya está registrado')
            return render(request, "inicio/registro.html", {
                'title': 'Registro',
                'tipos_identificacion': Tipoidentificacion.objects.all(),
            })

        # Validar si el correo ya existe
        if Usuario.objects.filter(correo=correoUser).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return render(request, "inicio/registro.html", {
                'title': 'Registro',
                'tipos_identificacion': Tipoidentificacion.objects.all(),
            })

        # Verificacion de datos enviados con FK
        # rol_obj = Rol.objects.get(idrol=rolUser)
        tipo_obj = Tipoidentificacion.objects.get(idtipoidentificacion=tipoIdentificacionUser)
        contrato_obj = Tipocontrato.objects.get(idcontrato=contratoUser)

        # Crear usuario
        registrarUsuario = Usuario(
            nombre=nombreUser,
            apellido=apellidoUser,
            rol=rolUser,
            tipoidentificacion=tipo_obj,
            numeroidentificacion=numeroIdentificacionUser,
            correo=correoUser,
            clave=claveUser,
            fecha=fechaRegistroUser,
            verificado=verificacionUser,
            contrato=contrato_obj,
            numerocontrato=numeroContrato
        )
        
        registrarUsuario.save()
        messages.success(request, 'Te has registrado exitosamente. Espera verificación.')
        return redirect('index')

    # Si es GET, muestra el formulario
    tipo_documento = Tipoidentificacion.objects.all()
    return render(request, "inicio/registro.html", {
        'title': 'Registro',
        'tipos_identificacion': tipo_documento,
    })
    
@login_required_custom
def asignacionInstructor(request):
    usuarios = Usuario.objects.filter(rol_id=1)
    return render(request, "inicio/asignacionInstructores.html",{
        'title':'Asignar instructor',
        'designatedUser': usuarios
    })
    
def asignar_instructor(request, idusuario):
    if request.method == "POST":
        try:
            # Instructor seleccionado
            instructor = Usuario.objects.get(idusuario=idusuario)

            # Coordinador logueado (var global)
            coordinador_id = request.session.get('user_id')

            if not coordinador_id:
                messages.error(request, "No se pudo identificar al coordinador logueado.")
                return redirect('asignar_instructor')

            coordinador = Usuario.objects.get(idusuario=coordinador_id)

            # Crear asignación
            Usuariosasignados.objects.create(
                idinstructor=instructor,
                idusuariocoordinador=coordinador,
                fechaasignacion=datetime.datetime.now()
            )

            messages.success(request, f"Instructor {instructor.nombre} asignado correctamente.")

        except Usuario.DoesNotExist:
            messages.error(request, "El usuario no existe.")
        except Exception as e:
            messages.error(request, f"Error al asignar instructor: {str(e)}")

    return redirect('asignar_instructor')