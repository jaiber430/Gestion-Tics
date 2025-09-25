from django.shortcuts import render, redirect
from django.contrib import messages
from Cursos.models import Usuario
import string, secrets
import datetime, calendar
from .models import Solicitud, Ficha, Estados, EstadosCoordinador, Solicitudcoordinador, Aspirantes
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
                rol=rol
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
            messages.error(request, "Usuario no encontrado o credenciales incorrectas")
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