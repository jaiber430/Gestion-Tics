from django.shortcuts import render
# Importar los modelos requeridos
from Cursos.models import Usuario
from django.contrib.auth import logout
from django.contrib import messages

# Create your views here.

def index(request):
    return render(request, "inicio/index.html",{
        'Title': 'Hi',
    })

def login_view(request):
    # Se asegutra de que los datos digitados y  enviados del formulario sean recibidos
    if request.method == "POST":
        numero_identificacion = request.POST.get("numeroCedula")
        clave = request.POST.get("clave")
        rol = int(request.POST.get("rol"))

        # Se asegura que los datos coincidan con los del modelo
        try:
            user = Usuario.objects.get(
                numeroidentificacion=numero_identificacion,
                clave=clave,
                rol=rol
            )

            # Guardar en sesión
            request.session['user_id'] = user.idusuario
            request.session['name'] = user.nombre

            # Definir layout para cada rol (Evita multiples archivos con el mismo contenido y diferente layout)
            if rol == 1:
                layout = "layout/layoutinstructor.html"
                rol_name = "Instructor"
            elif rol == 2:
                layout = "layout/layoutcoordinador.html"
                rol_name = "Coordinador"
            elif rol == 3:
                layout = "layout/layoutfuncionario.html"
                rol_name = "Funcionario"
            elif rol == 4:
                layout = "layout/layout_admin.html"
                rol_name = "Administrador"


            # Si todo esta en orden redirige a la pagina de inicio
            return render(request, "user/inicio.html", {
                "layout": layout,
                "rol": rol,
                "user": rol_name,
                "id": user.idusuario,
                "name": user.nombre,
            })

        # Si el usuario ingresa mal los caracteres o no existe se muestra este mensaje
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado o credenciales incorrectas")
            return render(request, "inicio/index.html")

    return render(request, "inicio/index.html")

