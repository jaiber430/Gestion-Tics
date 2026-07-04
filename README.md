# CampeSENA

Sistema web para la gestión y creación de cursos cortos del **SENA**, diseñado para digitalizar y automatizar los procesos que anteriormente se realizaban de forma manual. La plataforma centraliza la administración de solicitudes, aspirantes y programas curriculares, y genera automáticamente los documentos y archivos requeridos en cada etapa del proceso, reduciendo significativamente los márgenes de error y el tiempo operativo.

## Características principales

- Registro y seguimiento de solicitudes de cursos cortos (modalidad regular y campesina)
- Gestión de aspirantes con preinscripción en línea y control de cupos
- Generación automática de fichas de caracterización, cartas de solicitud, formatos de inscripción y archivos SOFIA Plus (PDF y Excel)
- Control de estados del proceso por roles: administrador, coordinador, funcionario e instructor
- Panel de reportes y consulta de solicitudes por rol
- Gestión de programas curriculares

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Framework web | Django 6.0 |
| Lenguaje | Python 3.12 |
| Base de datos | MySQL 8.0 |
| Servidor de aplicación | Gunicorn |
| Archivos estáticos | WhiteNoise |
| Generación de PDF | WeasyPrint |
| Generación de Excel | OpenPyXL |
| Contenedores | Docker + Docker Compose |

## Estructura de aplicaciones

| App | Responsabilidad |
|-----|----------------|
| `Cursos` | Usuarios, roles, autenticación y vistas principales |
| `solicitud` | Creación y gestión de solicitudes de cursos |
| `consultas` | Consultas por rol, fichas de caracterización y descargas |
| `aspirantes` | Preinscripción pública de aspirantes |
| `programas` | CRUD de programas curriculares |

---

## Requisitos previos

- Python 3.12+
- MySQL 8.0 (o Docker para ejecutar con contenedores)
- `pip` actualizado

---

## Instalación local (sin Docker)

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Gestion-Tics
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

> **Nota (Windows):** WeasyPrint requiere las bibliotecas GTK. Instálalas con MSYS2 siguiendo las instrucciones en `helpers/InstallMSYS2.txt`.

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto basándote en el siguiente ejemplo:

```env
SECRET_KEY=django-insecure-cambia-esto-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=complementario
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

ADMIN_EMAIL=admin@local.dev
ADMIN_PASSWORD=admin1234
ADMIN_NOMBRE=Administrador
ADMIN_APELLIDO=Sistema
ADMIN_DOCUMENTO=99999999
```

### 5. Importar la base de datos

```bash
mysql -u root -p complementario < CursosV17.sql
```

### 6. Aplicar migraciones

```bash
python manage.py migrate
```

### 7. Crear el usuario administrador inicial

```bash
python manage.py create_admin
```

### 8. Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

### 9. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

---

## Instalación con Docker Compose

### 1. Configurar variables de entorno

Crea el archivo `.env` en la raíz (ver ejemplo de la sección anterior). Agrega también:

```env
DB_ROOT_PASSWORD=root_segura
DB_EXTERNAL_PORT=3307
APP_PORT=8000
```

### 2. Construir e iniciar los servicios

```bash
docker compose up --build
```

Esto levanta dos servicios:

| Servicio | Descripción | Puerto |
|----------|-------------|--------|
| `db` | MySQL 8.0 con el script `CursosV17.sql` cargado automáticamente | `3307` (externo) |
| `app` | Django + Gunicorn con migraciones y admin creados al arrancar | `8000` |

### 3. Detener los servicios

```bash
docker compose down
```

Para eliminar también los volúmenes de datos:

```bash
docker compose down -v
```

---

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta de Django | (insegura de ejemplo) |
| `DEBUG` | Modo depuración | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por coma) | `localhost,127.0.0.1` |
| `DB_NAME` | Nombre de la base de datos | `complementario` |
| `DB_USER` | Usuario de MySQL | `root` |
| `DB_PASSWORD` | Contraseña de MySQL | *(vacío)* |
| `DB_HOST` | Host de MySQL | `localhost` |
| `DB_PORT` | Puerto de MySQL | `3306` |
| `DB_ROOT_PASSWORD` | Contraseña root (solo Docker) | — |
| `DB_EXTERNAL_PORT` | Puerto externo de MySQL (solo Docker) | `3307` |
| `APP_PORT` | Puerto externo de la app (solo Docker) | `8000` |
| `ADMIN_EMAIL` | Correo del administrador inicial | `admin@local.dev` |
| `ADMIN_PASSWORD` | Contraseña del administrador inicial | `admin1234` |
| `ADMIN_NOMBRE` | Nombre del administrador inicial | `Administrador` |
| `ADMIN_APELLIDO` | Apellido del administrador inicial | `Sistema` |
| `ADMIN_DOCUMENTO` | Documento del administrador inicial | `99999999` |

---

## Rutas principales

| Ruta | Descripción |
|------|-------------|
| `/` | Página de inicio / login |
| `/registro/` | Registro de usuarios |
| `/crearficha/` | Crear solicitud de curso |
| `/formulario_solicitud_regular/` | Solicitud modalidad regular |
| `/formulario_solicitud_campesina/` | Solicitud modalidad campesina |
| `/Consultas/` | Consultas según rol |
| `/ficha_caracterizacion/<id>/` | Ver ficha de caracterización |
| `/ficha_caracterizacion/<id>/pdf/` | Descargar ficha en PDF |
| `/preinscripcion/<id>/` | Formulario de preinscripción para aspirantes |
| `/reportes/` | Panel de reportes |
| `/admin/` | Panel de administración de Django |

---

## Seguridad

- Las credenciales de base de datos y la `SECRET_KEY` se gestionan exclusivamente mediante variables de entorno (`.env`). **Nunca** deben incluirse en el código fuente ni en el repositorio.
- En producción establece `DEBUG=False` y configura `ALLOWED_HOSTS` con el dominio real.
- Los archivos subidos por usuarios (PDFs, Excel) se almacenan en `media/` y nunca se sirven directamente sin control de acceso.