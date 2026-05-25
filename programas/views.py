from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from Cursos.models import Programaformacion, Area, Modalidad
from Cursos.views import login_required_custom

# Buscar programas
@login_required_custom
def buscar_programas(request):
    buscar = None
    area_seleccionada = None
    if request.method == "POST":
        programa = request.POST.get("programa", "").strip()
        area_id  = request.POST.get("area_filtro", "")
        area_seleccionada = area_id

        buscar = Programaformacion.objects.all()
        if programa:
            buscar = buscar.filter(nombreprograma__icontains=programa)
        if area_id:
            buscar = buscar.filter(idarea__idarea=area_id)

        if not buscar.exists():
            messages.error(request, "No existe un programa con las características dadas")

    # Traemos las áreas para el filtro y los modales
    areas = Area.objects.all()

    return render(request, "crud/buscar.html", {
        "buscar": buscar,
        "areas": areas,
        "area_seleccionada": area_seleccionada,
    })


# Editar programa
@login_required_custom
def editar_programa(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")  # Viene oculto desde el modal
        programa = get_object_or_404(Programaformacion, codigoprograma=codigo)

        # Actualizar campos básicos
        programa.verision = request.POST.get("version", programa.verision)
        programa.nombreprograma = request.POST.get("nombre", programa.nombreprograma)
        programa.horas = request.POST.get("horas", programa.horas)

        #  Actualizar relaciones (Area y Modalidad)
        area_id = request.POST.get("area")
        modalidad_id = request.POST.get("modalidad")

        if area_id:
            programa.idarea = get_object_or_404(Area, idarea=area_id)
        if modalidad_id:
            programa.idmodalidad = get_object_or_404(Modalidad, idmodalidad=modalidad_id)

        # Guardar cambios
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


# Crear programa
@login_required_custom
def crear_programa(request):
    if request.method == "POST":
        # Obtener datos del formulario
        codigo = request.POST.get("codigo")
        version = request.POST.get("version")
        nombre = request.POST.get("nombre")
        horas = request.POST.get("horas")
        area_id = request.POST.get("area")
        # Validar que no exista un programa con el mismo código
        if Programaformacion.objects.filter(codigoprograma=codigo).exists():
            messages.error(request, "Ya existe un programa con este código.")
            return redirect("crear_programa")

        try:
            # Obtener las relaciones
            area = get_object_or_404(Area, idarea=area_id)
            modalidad_id = request.POST.get("modalidad")
            if modalidad_id:
                modalidad = get_object_or_404(Modalidad, idmodalidad=modalidad_id)
            else:
                modalidad = Modalidad.objects.first()

            # Crear el nuevo programa
            nuevo_programa = Programaformacion(
                codigoprograma=codigo,
                verision=version,
                nombreprograma=nombre,
                horas=horas,
                idarea=area,
                idmodalidad=modalidad
            )
            nuevo_programa.save()
            messages.success(request, "Programa creado correctamente.")
            return redirect("buscar_programa")
        except Exception as e:
            messages.error(request, f"Error al crear el programa: {str(e)}")
            return redirect("crear_programa")

    # GET: Mostrar formulario de creación
    areas = Area.objects.all()

    return render(request, "crud/crear.html", {
        "areas": areas,
    })
