"""
Comando Django para crear o actualizar el usuario administrador inicial
del sistema (tabla 'usuario', rol=4, verificado=1).

Uso:
    python manage.py create_admin

Lee las variables de entorno:
    ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NOMBRE, ADMIN_APELLIDO, ADMIN_DOCUMENTO
"""

import os
import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from Cursos.models import Usuario, Rol, Tipoidentificacion


class Command(BaseCommand):
    help = 'Crea o actualiza el usuario administrador inicial del sistema'

    def handle(self, *args, **options):
        correo = os.environ.get('ADMIN_EMAIL', 'admin@local.dev')
        password = os.environ.get('ADMIN_PASSWORD', 'admin1234')
        nombre = os.environ.get('ADMIN_NOMBRE', 'Administrador')
        apellido = os.environ.get('ADMIN_APELLIDO', 'Sistema')

        try:
            documento = int(os.environ.get('ADMIN_DOCUMENTO', '99999999'))
        except ValueError:
            self.stderr.write(self.style.ERROR('ADMIN_DOCUMENTO debe ser un número entero.'))
            return

        # Verificar rol Administrador (id=4 según CursosV17.sql)
        try:
            rol = Rol.objects.get(idrol=4)
        except Rol.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    'El rol Administrador (idrol=4) no existe en la BD. '
                    'Verifica que se haya importado CursosV17.sql correctamente.'
                )
            )
            return

        # Obtener tipo de identificación (CC=id 2, fallback al primer disponible)
        try:
            tipo_id = Tipoidentificacion.objects.get(idtipoidentificacion=2)
        except Tipoidentificacion.DoesNotExist:
            tipo_id = Tipoidentificacion.objects.first()
            if tipo_id is None:
                self.stderr.write(
                    self.style.ERROR('No hay tipos de identificación en la BD.')
                )
                return

        # Buscar por correo (único) para decidir si crear o actualizar
        try:
            usuario = Usuario.objects.get(correo=correo)
            usuario.nombre = nombre
            usuario.apellido = apellido
            usuario.rol = rol
            usuario.tipoidentificacion = tipo_id
            usuario.clave = make_password(password)
            usuario.verificado = 1
            usuario.save()
            self.stdout.write(
                self.style.WARNING(f'Admin actualizado: {correo}')
            )
        except Usuario.DoesNotExist:
            # Verificar que el documento no esté ocupado por otro usuario
            if Usuario.objects.filter(numeroidentificacion=documento).exists():
                self.stderr.write(
                    self.style.ERROR(
                        f'El documento {documento} ya está registrado para otro usuario. '
                        'Ajusta ADMIN_DOCUMENTO en el .env.'
                    )
                )
                return

            Usuario.objects.create(
                nombre=nombre,
                apellido=apellido,
                rol=rol,
                tipoidentificacion=tipo_id,
                numeroidentificacion=documento,
                correo=correo,
                clave=make_password(password),
                fecha=datetime.date.today(),
                verificado=1,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Admin creado exitosamente: {correo}')
            )
