# 📚 Documentación Personal — Backend IA Tambo360

> **Autor:** Tomi   

## 🧠 ¿Para qué existe este backend?

Este servicio es el **cerebro de IA** del sistema Tambo360. Se encarga de analizar datos productivos de tambos lecheros y generar observaciones asistidas por inteligencia artificial.

**Rol dentro del sistema completo:**
- Es un servicio **independiente y desacoplado** del backend principal de Tambo360.
- El backend principal le envía datos estructurados por HTTP.
- Este servicio consulta un modelo de IA externo (vía OpenRouter), valida la respuesta y la devuelve.
- **No tiene acceso** a la base de datos del backend principal ni al frontend.
- Tiene su propia base de datos para guardar resultados.

```
Usuario → Frontend (SPA)
               │
               ▼
      Backend Principal (Next.js + Prisma + PostgreSQL)
               │  POST /api/v1/tambo/analyze
               ▼
      [ESTE SERVICIO — Python + FastAPI]   ←→  Su propia BD
               │
               ▼
      OpenRouter → Modelo de IA (LLM)
               │
               ▼
      Respuesta JSON validada (análisis de producción)
```

---

## 🗃️ Modelo de datos del backend principal

El backend principal tiene estas entidades en PostgreSQL (Prisma). Esto es lo que puede enviarnos para analizar:

| Entidad | Para qué |   
|---|---|
| `Usuario` | El productor dueño de los establecimientos |
| `Establecimiento` | El tambo / planta productiva del usuario |
| `Producto` | Lo que se produce: quesos o leches |
| `LoteProduccion` | Un lote de producción: cantidad, fecha, producto |
| `Merma` | Pérdida dentro de un lote (ej: corte defectuoso) |
| `CostosDirecto` | Costo asociado a un lote (ej: leche cruda, energía) |

Nosotros **no accedemos directamente a esta BD**. El backend nos manda los datos ya consultados en el body del request.

---

## 🛠️ Stack tecnológico

| Tecnología | Para qué sirve |
|---|---|
| **Python 3.11** | Lenguaje principal del proyecto |
| **FastAPI** | Framework web que expone la API REST (los endpoints) |
| **Pydantic** | Valida que los datos de entrada y salida tengan el formato correcto |
| **Uvicorn** | Servidor web que corre la aplicación FastAPI |
| **httpx** | Cliente HTTP asíncrono para llamar a la API de OpenRouter |
| **OpenRouter** | Gateway que nos da acceso a múltiples modelos de IA (DeepSeek, GPT-4, Claude, etc.) |
| **python-dotenv** | Lee las variables de entorno del archivo `.env` |
| **Docker** | Para correr el servicio en contenedores (producción) |

---

## 📁 Estructura del proyecto

```
i006-tambo360-ai/
│
├── main.py                  # Punto de entrada de la app. Configura FastAPI, CORS y arranca el servidor.
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py      # Endpoints de chat genérico con la IA
│   │       ├── health.py    # Endpoint para verificar que el servicio está vivo
│   │       └── tambo.py     # (próximo) Endpoint de análisis TamboEngine
│   │
│   ├── config/
│   │   └── settings.py      # Lee las variables de entorno (.env) y las expone al resto del código
│   │
│   ├── core/
│   │   ├── logging.py       # Configura el sistema de logs
│   │   └── security.py      # Utilidades de seguridad (ej: ocultar la API key en los logs)
│   │
│   ├── models/
│   │   └── schemas.py       # Define los modelos de datos (qué puede recibir y devolver la API)
│   │
│   └── services/
│       ├── ai_service.py    # Se conecta a OpenRouter y hace las llamadas al modelo de IA
│       └── tambo_engine.py  # (Posible desarrollo, dejo una opinion al final) Lógica específica de análisis de tambos
│
├── .env                     # Variables de entorno: API keys, configuración (NO commitear)
├── requirements.txt         # Dependencias Python (para instalar con pip)
├── pyproject.toml           # Configuración del proyecto (para uv)
├── Dockerfile               # Configuración para containerizar con Docker
└── docker-compose.yml       # Para levantar el servicio con Docker Compose
```

---

## 🔌 Endpoints actuales

| Método | URL | Qué hace |
|---|---|---|
| `GET` | `/` | Bienvenida: devuelve nombre y versión de la app |
| `GET` | `/api/v1/health` | Health check: confirma que el servicio está corriendo |
| `GET` | `/api/v1/chat/models` | Lista los modelos de IA disponibles en OpenRouter |
| `POST` | `/api/v1/chat/completions` | Envía un mensaje a la IA y recibe respuesta |

---

## 🤖 ¿Cómo funciona la llamada a la IA?

1. Alguien hace un `POST /api/v1/chat/completions` con un mensaje.
2. FastAPI recibe el request y lo valida con Pydantic.
3. Se llama a `ai_service.chat_completion()`.
4. El `ai_service` empaqueta el mensaje y se lo manda a OpenRouter via HTTP.
5. OpenRouter lo envía al modelo elegido (ej: `arcee-ai/trinity-large-preview:free`).
6. El modelo responde, `ai_service` valida la respuesta con Pydantic.
7. El resultado se devuelve al cliente en JSON.

---

## ⚙️ Variables de entorno (archivo `.env`)

| Variable | Obligatoria | Para qué |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ Sí | Clave secreta para usar OpenRouter |
| `OPENROUTER_BASE_URL` | No | URL de la API de OpenRouter (ya tiene valor por defecto) |
| `APP_NAME` | No | Nombre en el Swagger y en los logs |
| `DEBUG` | No | `true` = recarga automática al editar código |
| `API_PORT` | No | Puerto donde corre el servidor (default: 8000) |
| `CORS_ORIGINS` | No | Qué frontends pueden llamar a esta API |

---

## 🚀 Cómo arrancar el servidor

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Arrancar el servidor con recarga automática
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Después podés entrar a **http://localhost:8000/docs** para ver y probar los endpoints.
Principal a probar es el endpoint `/api/v1/chat/completions`, este genera la respuesta de la IA.


---

## 📌 Conceptos clave que aprendí

- **FastAPI** actúa como el "camarero": recibe los pedidos, los valida y los entrega.
- **Pydantic** actúa como el "portero": no deja pasar datos con formato incorrecto.
- **ai_service** actúa como el "cocinero": habla con OpenRouter y trae la respuesta de la IA.
- **OpenRouter** es el "proveedor": da acceso a muchos modelos de IA sin tener que contratar cada uno por separado.
- El modelo de IA **no sabe nada del negocio** por sí solo — nosotros le damos el contexto a través del **prompt**.
- **Temperature 0** = respuestas determinísticas (siempre igual dado el mismo input). Ideal para análisis técnico.

---

## 🔨 Posible implementacion de `tambo_engine.py`

Esto seria el módulo central del servicio. Su objetivo seria recibir datos productivos de un tambo, consultarle al modelo de IA y devolver un análisis estructurado de desvíos.

### ¿Qué habria que hacer?

**1. Definir los schemas en `schemas.py`**
- `TamboAnalysisInput` — lo que el backend nos envía (período, litros reales, litros esperados, grasa, proteína, vacas en ordeñe, etc.)
- `TamboAnalysisOutput` — lo que la IA debe devolver (estado general, resumen, lista de desvíos, recomendaciones)
- `DesvioProductivo` — un ítem dentro de la lista de desvíos (indicador, valor real, valor esperado, descripción)

**2. Crear `tambo_engine.py` en `app/services/`**
- `build_prompt(input)` → Arma el prompt con los datos reales del tambo. Le dice al modelo exactamente qué analizar y en qué formato JSON debe responder.
- `call_model(prompt)` → Llama a OpenRouter usando el `ai_service` que ya existe, con `temperature=0`.
- `validate_response(raw)` → Parsea el JSON devuelto por el modelo y lo valida con Pydantic. Si la estructura no es la esperada, lanza un error.
- `analyze(input)` → Orquesta todo el flujo: build → call → validate → return.

**3. Crear `tambo.py` en `app/api/v1/`**
- Expone el endpoint `POST /api/v1/tambo/analyze`
- Recibe un `TamboAnalysisInput`, llama al TamboEngine y devuelve un `TamboAnalysisOutput`
- Si el modelo falla o devuelve algo inválido → responde con HTTP 503 (sin romper el sistema)

**4. Registrar el router en `app/api/v1/__init__.py`**

### Flujo completo una vez implementado

```
Backend principal
       │
       ▼
POST /api/v1/tambo/analyze  (con datos del tambo)
       │
       ▼
TamboEngine.analyze()
   ├─ build_prompt()      → construye el prompt con contexto real
   ├─ call_model()        → llama a OpenRouter (temperature=0)
   ├─ validate_response() → verifica que el JSON sea correcto
       │
       ▼
TamboAnalysisOutput (JSON validado)
```

---

## 🌿 Rama: `2-revisión-y-adaptación-de-los-schema-pydantic-existentes`

**Objetivo:** Preparar la capa de datos del servicio de IA para el módulo TamboEngine.

### ¿Qué se implementó?

**`requirements.txt`** — Se agregaron las dependencias de base de datos:
- `sqlalchemy==2.0.23` → ORM para interactuar con la BD
- `aiosqlite==0.19.0` → Driver SQLite asíncrono (compatible con FastAPI async)

**`app/database.py`** *(archivo nuevo)* — Configura el motor de base de datos SQLite asíncrono. Incluye:
- `init_db()`: crea las tablas al iniciar la app
- `get_db()`: dependencia de FastAPI que provee una sesión de BD por request

**`app/models/db_models.py`** *(archivo nuevo)* — Define la tabla `alertas` en la base de datos con SQLAlchemy. Guarda el resultado de cada análisis de IA:  
`id` · `id_establecimiento` · `periodo` · `estado_general` · `resumen_ejecutivo` · `desvios_json` · `recomendaciones_json` · `creado_en`

**`app/models/schemas.py`** — Se agregaron los schemas Pydantic de TamboEngine:

| Schema | Tipo | Para qué |
|---|---|---|
| `MermaInput` | Input | Una merma dentro de un lote |
| `CostoDirectoInput` | Input | Un costo directo dentro de un lote |
| `LoteInput` | Input | Un lote de producción del backend principal |
| `TamboAnalysisInput` | Input | El payload completo que envía el backend para analizar |
| `DesvioDetectado` | Output | Un desvío productivo detectado por la IA |
| `TamboAnalysisOutput` | Output | Respuesta completa del análisis de IA |
| `AlertaResponse` | Output | Lo que devuelve el endpoint GET /alertas |

> Los schemas de input están **alineados con el schema Prisma del backend principal** (entidades `LoteProduccion`, `Merma`, `CostosDirecto`).

---

## 🌿 Rama: `3-implementación-guiada-de-un-endpoint-de-ia-simple`

**Objetivo:** Implementar el servicio TamboEngine y los endpoints de análisis (HU3) y consulta de alertas (HU4).

### ¿Qué se implementó?

**`app/services/tambo_engine.py`** *(archivo nuevo)* — Servicio central de análisis con IA. Contiene 4 funciones:
- `build_prompt(data)`: arma el system prompt con rol de analista + los datos reales de los lotes en texto legible + el contrato JSON que el modelo debe devolver
- `call_model(messages)`: llama a OpenRouter via `ai_service` con `temperature=0.1` 
- `validate_response(raw, data)`: limpia posible markdown del response, parsea el JSON y valida con Pydantic. Fuerza que los IDs coincidan con el input
- `analyze(data)`: orquesta todo el flujo → build → call → validate → return

**`app/api/v1/tambo.py`** *(archivo nuevo)* — Dos endpoints:

| Método | URL | HU | Qué hace |
|---|---|---|---|
| `POST` | `/api/v1/tambo/analyze` | HU3 | Recibe datos, ejecuta el análisis con IA y guarda el resultado como alerta en SQLite |
| `GET` | `/api/v1/tambo/alertas/{idEstablecimiento}` | HU4 | Devuelve todas las alertas guardadas para un establecimiento, ordenadas por fecha DESC |

> Si la IA falla, el endpoint responde **HTTP 503** para no romper el backend principal.

**`app/api/v1/__init__.py`** — Se registró `tambo.router` junto a los existentes (chat, health).

**`main.py`** — Se agregó `await init_db()` en el startup para que la tabla `alertas` se cree automáticamente al arrancar.
