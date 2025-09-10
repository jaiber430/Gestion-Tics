"""
URL configuration for Gestion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Cursos import views
from solicitud import views as views_solicitud
from consultas import views as views_consultas
# from aspirantes import views as views_aspirantes
from aspirantes import views as views_aspirantes
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #Paginas princiales Login - Pagina inicio (Todos los roles)
    path('admin/', admin.site.urls),
    path('', views.index, name="index"),
    path('pagina_principal/', views.login_view, name="login"),
    # Paginas de creación (Admin - Instru)
    path('crearficha/', views_solicitud.crear_solicitud, name="Crearsolicitud"),
    path('formulario_solicitud_regular/', views_solicitud.solicitud_regular, name="crearregular"),
    path('formulario_solicitud_campesina/', views_solicitud.solicitud_campesina, name="crearcampesina"),
    path('Consultas_instructor/', views_consultas.consultas_instructor, name="consultas_instructor"),
    path('ficha_caracterizacion/<int:solicitud_id>/', views_consultas.ficha_caracterizacion, name="ficha_caracterizacion"),
    path('ficha_caracterizacion/<int:solicitud_id>/pdf/', views_consultas.ficha_caracterizacion_pdf, name="ficha_caracterizacion_pdf"),
    path('preinscripcion/<int:idsolicitud>/', views_aspirantes.formulario_aspirantes, name="formularioaspirantes"),
    path('preinscripcion/', views_aspirantes.registro_aspirante, name="Registroaspirantes"),
    path('pdf/<int:id>/<int:idrol>', views_consultas.descargar_pdf, name='descargar_pdf'),
    path('exportar-excel/<int:idsolicitud>', views_consultas.generar_excel, name='exportar_excel'),
    path('descargar_excel/<int:id>/<int:idrol>', views_consultas.descargar_excel, name="descargar_excel"),
    path('descargar_carta/<int:id>/<int:idrol>', views_consultas.descargar_carta, name="descargar_carta"),
    path('revision_funcionario/<int:id>/', views_consultas.revision_fichas, name="ficha_funcionario")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
