from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from Cursos.models import Programaformacion, Area, Modalidad
from Cursos.views import login_required_custom

# Buscar programas
@login_required_custom
def buscar_programas(request):
    buscar = None
    if request.method == "POST":
        programa = request.POST.get("programa")
        buscar = Programaformacion.objects.filter(nombreprograma__icontains=programa)

        # 🔹 Si no existe ningún programa, mandamos un mensaje
        if not buscar.exists():
            messages.error(request, "No existe un programa con las carcateristicas dadas")

    # 🔹 Traemos las áreas para el modal de agregar
    areas = Area.objects.all()

    return render(request, "crud/buscar.html", {
        "buscar": buscar,
        "areas": areas
    })


# Editar programa
@login_required_custom
def editar_programa(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")  # Viene oculto desde el modal
        programa = get_object_or_404(Programaformacion, codigoprograma=codigo)

        # 🔹 Actualizar campos básicos
        programa.verision = request.POST.get("version", programa.verision)
        programa.nombreprograma = request.POST.get("nombre", programa.nombreprograma)
        programa.horas = request.POST.get("horas", programa.horas)

        # 🔹 Actualizar relaciones (Area y Modalidad)
        area_id = request.POST.get("area")
        modalidad_id = request.POST.get("modalidad")

        if area_id:
            programa.idarea = get_object_or_404(Area, idarea=area_id)
        if modalidad_id:
            programa.idmodalidad = get_object_or_404(Modalidad, idmodalidad=modalidad_id)

        # 🔹 Guardar cambios
        programa.save()
        messages.success(request, "Programa actualizado correctamente.")
        return redirect("buscar_programa")  # Redirige al listado después de editar

    # Si no es POST no debería usarse, pero lo dejamos por si acaso
    messages.error(request, "Método no permitido para esta vista.")
    return redirect("buscar_programa")


# Borrar programa
@login_required_custom
def borrar_programa(request, codigo):
    programa = get_object_or_404(Programaformacion, codigoprograma=codigo)
    programa.delete()
    messages.success(request, "Programa eliminado correctamente.")
    return redirect("buscar_programa")
