# 🎓 Smart Campus Vision — Gestión de Espacios y Visión Artificial

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" alt="Python 3.13">
  <img src="https://img.shields.io/badge/Django-5.2-darkgreen?style=for-the-badge&logo=django" alt="Django 5.2">
  <img src="https://img.shields.io/badge/React-19-149ECA?style=for-the-badge&logo=react" alt="React 19">
  <img src="https://img.shields.io/badge/TypeScript-5.7-blue?style=for-the-badge&logo=typescript" alt="TypeScript 5.7">
  <img src="https://img.shields.io/badge/FastAPI-Microservicio-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/YOLO11-OpenCV-purple?style=for-the-badge" alt="YOLO11 y OpenCV">
  <img src="https://img.shields.io/badge/Estado-En_Desarrollo-orange?style=for-the-badge" alt="En desarrollo">
</p>

---

# 📖 Descripción

Proyecto académico de gestión universitaria desarrollado con **Django y Django REST Framework**, una interfaz **React con TypeScript** y un microservicio de visión artificial con **FastAPI, YOLO y OpenCV**.

Permite gestionar **aulas y laboratorios**, analizar su ocupación mediante videos o una cámara local, registrar capacidades validadas y recomendar asignaciones compatibles con los cursos, horarios y recursos disponibles. Incluye autenticación, roles, alertas, historial, decisiones auditadas y reportes PDF.

Los **hitos 1 a 8 están implementados**. La evaluación de precisión, la verificación con PostgreSQL y el despliegue real en AWS siguen pendientes. El proyecto todavía no está listo para producción; consulta el [estado verificable y la entrega al grupo](docs/estado-y-entrega.md).

---

# 🎯 Objetivos del Proyecto

✅ Construir una API con Django REST Framework, autenticación y permisos.  
✅ Separar la interfaz web, el backend y el microservicio de visión.  
✅ Integrar visión artificial para detectar personas y analizar ocupación.  
✅ Validar capacidades de aulas y laboratorios con trazabilidad.  
✅ Recomendar espacios según matrícula, equipamiento y disponibilidad.  
✅ Detectar conflictos de aula, docente y curso al gestionar asignaciones.  
✅ Generar reportes PDF y conservar el historial de análisis y decisiones.  
✅ Preparar la arquitectura para su posterior despliegue en AWS.

---

# 🛠️ Tecnologías Utilizadas

| Tecnología | Uso |
| --- | --- |
| Python 3.13 | Backend y procesamiento de visión |
| Django 5.2 | Modelos, autenticación y administración |
| Django REST Framework 3.16 | API y validación de solicitudes |
| React 19 y TypeScript | Interfaz web responsive |
| Vite 6 | Desarrollo y compilación del frontend |
| FastAPI | API interna del microservicio |
| Ultralytics YOLO11n y OpenCV | Detección y procesamiento de imágenes y videos |
| PostgreSQL / SQLite | Base prevista para despliegue / desarrollo local verificado |
| ReportLab | Reportes PDF |
| Playwright | Pruebas de navegador |
| Docker Compose | Configuración de servicios y despliegue |
| AWS | Destino requerido; despliegue real pendiente |

---

# 📂 Estructura del Proyecto

```text
SmartCampusVisionSystem/
│
├── backend/                         ← API y lógica de negocio
│   ├── manage.py                    ← Punto de entrada Django
│   ├── requirements.lock.txt        ← Dependencias fijadas
│   ├── config/                      ← Configuración y rutas
│   ├── accounts/                    ← Usuarios, sesiones, roles y permisos
│   ├── campus/                      ← Aulas, cursos, alertas y asignaciones
│   └── video_analysis/              ← Análisis, cámara y reportes
│
├── frontend/
│   ├── package.json                 ← Dependencias y comandos
│   ├── src/                         ← Pantallas, componentes y cliente API
│   └── tests/                       ← Pruebas de navegador
│
├── services/vision/                 ← Microservicio de visión
│   ├── app/                         ← API, detector, procesamiento y cola
│   ├── models/                      ← Pesos locales; fuera de Git
│   ├── tests/                       ← Pruebas de procesamiento y evaluación
│   └── README.md                    ← Instalación del servicio
│
├── docs/                            ← Requisitos, hitos y evidencias
├── deploy/                          ← Archivos de despliegue
├── .vscode/                         ← Tareas de desarrollo
├── .env.example                     ← Plantilla de configuración
├── compose.yaml                     ← Servicios de desarrollo
├── compose.deploy.yaml              ← Pila prevista para despliegue
└── README.md
```

---

# 🗃️ Modelos y Relaciones

| Modelo | Relaciones principales |
| --- | --- |
| `User` | Usuario personalizado con correo y rol |
| `Classroom` | ForeignKey → usuario que valida la capacidad |
| `CapacityValidation` | ForeignKey → Classroom, User |
| `ClassroomAvailability` | ForeignKey → Classroom |
| `Teacher` / `Subject` | Catálogos de docentes y asignaturas |
| `Course` | ForeignKey → Subject, Teacher |
| `CourseMeeting` | ForeignKey → Course |
| `Analysis` | ForeignKey → Classroom |
| `VideoJob` | ForeignKey → Classroom, Course, User / OneToOne → Analysis |
| `Alert` | ForeignKey → Analysis, User |
| `AlertEvent` | ForeignKey → Alert, User |
| `AssignmentProposal` | ForeignKey → Course, Classroom, User |
| `AssignmentDecision` | ForeignKey → AssignmentProposal, User |
| `SystemSettings` / `AssignmentRule` | Configuración y reglas de asignación |
| `AdministrativeEvent` | ForeignKey → User; conserva cambios anteriores y posteriores |

---

# 🔐 Arquitectura y Código Reutilizable

| Componente | Responsabilidad |
| --- | --- |
| Modelos y ORM | Persistencia, relaciones y restricciones |
| Serializadores | Validación de entradas y representación de respuestas |
| Vistas y rutas | Gestión de solicitudes HTTP |
| Servicios | Casos de uso y reglas de negocio |
| Permisos | Autorización por usuario y operación |
| Microservicio | Inferencia y procesamiento separados de Django |

Django se comunica con visión mediante HTTP y la clave interna `VISION_API_KEY`, que no se entrega al navegador. El procesamiento de videos requiere el microservicio y el trabajador `run_video_worker`.

Los roles son **Administrador**, **Coordinador** y **Consulta**. El registro público crea cuentas de consulta. El rol de aplicación y `is_staff` de Django son distintos; las operaciones disponibles dependen de los permisos del usuario.

---

# ▶️ Instalación del Proyecto

Requisitos de referencia: **Python 3.13** y **Node.js 22.11**, o versiones compatibles con las dependencias fijadas. Ejecuta los comandos en **PowerShell**, desde la raíz del proyecto.

## Crear el entorno e instalar el backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item .env.example .env
```

Si ya tienes un `.env` configurado, consérvalo. Define una `DJANGO_SECRET_KEY` aleatoria y una `VISION_API_KEY` distinta y aleatoria. No uses los valores de ejemplo ni publiques el archivo.

Para desarrollo sin PostgreSQL, configura en `.env`:

```dotenv
DATABASE_ENGINE=sqlite
DJANGO_DEBUG=true
```

## Instalar el frontend

```powershell
cd frontend
npm.cmd ci
cd ..
```

## Preparar el microservicio

Instala el entorno independiente de visión y descarga los pesos siguiendo [services/vision/README.md](services/vision/README.md). La guía incluye los comandos y las variables del detector.

## Aplicar migraciones y crear un administrador

```powershell
.\.venv\Scripts\python.exe backend/manage.py migrate
.\.venv\Scripts\python.exe backend/manage.py createsuperuser
```

No existe una contraseña administrativa predeterminada. Puedes registrarte desde la interfaz para crear una cuenta de consulta. Para asignar el rol administrador a una cuenta existente sin cambiar su contraseña:

```powershell
.\.venv\Scripts\python.exe backend/manage.py set_role correo@ejemplo.edu admin
```

Recarga la interfaz después del cambio.

---

# 🚀 Ejecución del Proyecto

Ejecuta cada bloque en una terminal independiente, partiendo de la raíz.

## Servidor Django

```powershell
.\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

## Interfaz React

```powershell
cd frontend
npm.cmd run dev
```

## Microservicio de visión

```powershell
.\services\vision\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/vision --host 127.0.0.1 --port 8002
```

## Trabajador de videos

```powershell
.\.venv\Scripts\python.exe backend/manage.py run_video_worker
```

| Acceso | Dirección |
| --- | --- |
| Aplicación | http://localhost:5173 |
| Administración Django | http://localhost:8000/admin/ |
| Salud del microservicio | http://127.0.0.1:8002/health |

También puedes usar **Terminal → Ejecutar tarea → Iniciar Smart Campus Vision** en Visual Studio Code para iniciar los cuatro procesos. Si ya están activos, no los inicies de nuevo. Para detenerlos, pulsa **Ctrl+C** en cada terminal.

En **Análisis → Cargar video**, selecciona un aula, carga un MP4/AVI y pulsa **Iniciar análisis**. Al finalizar, **Guardar resultado** incorpora el resumen al dashboard y al aula. La descarga JSON incluye conteos por fotograma y la identidad del modelo.

---

# 📋 Funcionalidades del Sistema

| Módulo | Operaciones disponibles |
| --- | --- |
| Usuarios | Registro, login, logout, perfil, cambio y recuperación de contraseña |
| Administración | Gestión de acceso, configuración y auditoría |
| Dashboard | Indicadores y ocupación desde análisis guardados |
| Aulas y laboratorios | Registro, consulta, edición, equipamiento y disponibilidad |
| Capacidad | Validación manual con responsable, fecha e historial |
| Datos académicos | Docentes, asignaturas, cursos, matrícula y franjas horarias |
| Videos | Carga, análisis, progreso, cancelación, vista anotada y JSON |
| Cámara local | Análisis por muestras y guardado de sesiones |
| Historial y alertas | Filtros, seguimiento de estados y eventos auditados |
| Asignaciones | Alternativas compatibles, propuestas y decisiones con motivo |
| Calendario | Ocupación planificada y conflictos |
| Reglas | Parámetros y preferencias editables |
| Reportes | PDF individuales y consolidados con filtros y resúmenes |

> Los conteos requieren evaluación con anotaciones humanas. El detector general usa la clase `tv` como referencia de monitores; no equivale a puestos utilizables ni acredita capacidad física automática. La capacidad utilizada debe validarse manualmente.

---

# ⚙️ Configuración Adicional

## PostgreSQL

La configuración predeterminada utiliza PostgreSQL. Si tienes Docker:

1. Define las variables `POSTGRES_*` en `.env`, incluida una contraseña propia.
2. Configura `DATABASE_ENGINE=postgresql`.
3. Ejecuta `docker compose up -d db` desde la raíz.
4. Aplica las migraciones y ejecuta las pruebas antes de iniciar la aplicación.

También puedes usar un servidor PostgreSQL existente. Cambiar de base no copia automáticamente las cuentas de SQLite. La ejecución local documentada se verificó con SQLite; PostgreSQL sigue pendiente de verificación.

## Recuperación de contraseña

En desarrollo, los correos se guardan en `backend/local-mail/`. Solicita recuperación para una cuenta existente, abre el archivo recién generado y copia el enlace al navegador. Los enlaces caducan en una hora; cambiar la contraseña invalida las otras sesiones.

Para envío real, configura `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` y `DEFAULT_FROM_EMAIL`. SMTP externo aún no se ha probado.

---

# 🧪 Pruebas del Proyecto

## Backend

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe backend/manage.py test accounts campus video_analysis
```

## Frontend y navegador

```powershell
cd frontend
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Las pruebas de navegador inician servidores propios en **8001 y 5174**, utilizan `backend/e2e.sqlite3` y crean cuentas `browser-...@example.edu` separadas de la base de la aplicación. Los puertos deben estar libres.

## Microservicio

```powershell
cd services/vision
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

La evidencia de verificaciones anteriores está en [Estado y entrega](docs/estado-y-entrega.md). Las pruebas con detectores de prueba no certifican la precisión del modelo real.

---

# ☁️ Estado y Despliegue

La entrega requiere evaluar conteos con datos anotados, medir rendimiento en el equipo de presentación, verificar PostgreSQL y la pila Linux, configurar SMTP y desplegar en AWS.

Antes de producción también deben validarse HTTPS, almacenamiento de videos, escalado de inferencia, caché compartida para límites de solicitudes, observabilidad, backups y restauración. Los límites actuales usan la caché local de Django para desarrollo de un proceso.

Los números, usuarios, fechas y detecciones de `docs/referencias/` son ejemplos del prototipo visual y no constituyen resultados reales.

---

# 📚 Documentación del Proyecto

| Documento | Contenido |
| --- | --- |
| [Alcance y validación](docs/alcance-y-validacion.md) | Requisitos y criterios de verificación |
| [Hito 1](docs/hito-1.md) | Acceso y dashboard |
| [Hito 2](docs/hito-2.md) | Aulas y datos académicos |
| [Hito 3](docs/hito3-video.md) | Análisis de videos |
| [Hito 4](docs/hito4-historial-alertas.md) | Historial y alertas |
| [Hito 5](docs/hito5-asignacion-horarios.md) | Asignaciones y horarios |
| [Hito 6](docs/hito6-reportes.md) | Reportes PDF |
| [Hito 7](docs/hito7-camara.md) | Cámara local |
| [Hito 8](docs/hito8-cierre-funcional.md) | Configuración y cierre funcional |
| [Videos y modelo](docs/videos-y-modelo.md) | Muestras y límites del detector |
| [Evaluación del modelo](docs/evaluacion-modelo.md) | Comparación con anotaciones humanas |
| [Estado y entrega](docs/estado-y-entrega.md) | Evidencia y pendientes del grupo |
| [Despliegue AWS](docs/despliegue-aws.md) | Preparación de Docker y HTTPS |

---

# 🤖 Uso de Inteligencia Artificial

Para adaptar este `README` se utilizó **Codex (OpenAI)** como apoyo para revisar la estructura del repositorio, contrastar tecnologías y modelos, y organizar la documentación siguiendo el estilo del README de referencia.

La inteligencia artificial integrada en la aplicación corresponde al detector **YOLO**, utilizado junto con **OpenCV** para procesar imágenes y videos.

---


# ⭐ Recomendación

Si el proyecto te resulta útil, puedes darle una ⭐ al repositorio para apoyar el trabajo realizado.
