# 🚀 GUÍA DETALLADA: MIGRACIÓN PYTHON FASTAPI → TYPESCRIPT/EXPRESS

> **Este documento describe EXACTAMENTE cómo funciona el backend Python actual.**
> **Pasa este archivo completo a ChatGPT para que entienda la arquitectura y pueda guiarte en la migración.**

---

## 📊 ARQUITECTURA GENERAL: FLUJO DE DATOS END-TO-END

### Visión de 30.000 pies

```
┌──────────────────────────────────────────────────────────────────────┐
│                        EXPRESS FRONTEND                              │
│                                                                        │
│  POST /api/analyze o GET /alertas                                    │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 │ HTTP Request (JSON)
                                 ↓
        ┌──────────────────────────────────────────┐
        │     FASTAPI BACKEND (PYTHON)             │
        │     puerto 8000                          │
        │                                          │
        │  ┌────────────────────────────────────┐  │
        │  │ 1. Validación de datos             │  │ (Pydantic schemas)
        │  │    - ChatRequest, TamboAnalysisInput  │
        │  └────────────────────────────────────┘  │
        │           ↓                              │
        │  ┌────────────────────────────────────┐  │
        │  │ 2. Lógica de negocio               │  │
        │  │    - TamboEngine (cálculos puros)  │  │
        │  │    - AIService (OpenRouter client) │  │
        │  └────────────────────────────────────┘  │
        │           ↓                              │
        │  ┌────────────────────────────────────┐  │
        │  │ 3. Acceso a BD                     │  │
        │  │    - SQLAlchemy ORM                │  │
        │  │    - Async SQL queries             │  │
        │  └────────────────────────────────────┘  │
        │           ↓                              │
        │  ┌────────────────────────────────────┐  │
        │  │ 4. Respuesta JSON                  │  │
        │  │    - TamboAnalysisOutput           │  │
        │  │    - ChatResponse                  │  │
        │  └────────────────────────────────────┘  │
        └──────────────────────────────────────────┘
                     ↓
        ┌──────────────────────┐
        │ OpenRouter API       │
        │ (LLM calls)          │
        └──────────────────────┘
                     ↓
        ┌──────────────────────┐
        │ SQLite/PostgreSQL    │
        │ (Base de datos)      │
        └──────────────────────┘
```

---

## 📁 ESTRUCTURA DE CARPETAS Y ARCHIVOS

```
tambo360-ia/
├── main.py                          # Punto de entrada (uvicorn)
├── requirements.txt                 # Dependencias Python
├── .env                             # Variables de entorno
├── docker-compose.yml               # Contenedores
├── Dockerfile                       # Imagen Docker
│
└── app/
    ├── __init__.py
    │
    ├── database.py                  # ⚙️ Configuración de BD (SQLAlchemy)
    │
    ├── api/
    │   ├── __init__.py
    │   ├── dependencies.py          # 🔌 Inyección de dependencias (FastAPI)
    │   └── v1/
    │       ├── __init__.py
    │       ├── chat.py              # 💬 Endpoints de chat (OpenRouter)
    │       ├── health.py            # 🏥 Health check
    │       └── tambo.py             # 📊 Endpoints de análisis
    │
    ├── config/
    │   ├── __init__.py
    │   └── settings.py              # ⚙️ Configuración (variables de entorno)
    │
    ├── core/
    │   ├── __init__.py
    │   ├── logging.py               # 📝 Sistema de logging
    │   └── security.py              # 🔐 Funciones de seguridad
    │
    ├── models/
    │   ├── __init__.py
    │   ├── db_models.py             # 🗄️ Modelos SQLAlchemy (Alerta, PromedioCategoria)
    │   └── schemas.py               # 📋 DTOs y validación (Pydantic)
    │
    └── services/
        ├── __init__.py
        ├── ai_service.py            # 🤖 Cliente HTTP a OpenRouter
        └── tambo_engine.py          # 🧮 Lógica de cálculos y análisis
```

---

## 🔄 FLUJOS PRINCIPALES

### FLUJO 1: POST /api/v1/chat/completions (Chat simple con IA)

**Archivo**: `app/api/v1/chat.py`

```
1. Frontend envía:
   POST /api/v1/chat/completions
   Body: {
     model: "arcee-ai/trinity-large-preview:free",
     messages: [{role: "user", content: "¿Hola?"}],
     max_tokens: 1000,
     temperature: 0.7
   }

2. FastAPI recibe (validación con Pydantic):
   - ChatRequestSchema valida los datos
   - Si falla validación → error 422

3. FastAPI ejecuta:
   - @router.post("/completions")
   - Llama a: aiService.chatCompletion(request)

4. AIService.chatCompletion():
   app/services/ai_service.py → ChatRequest → OpenRouter API
   
   a) Prepara payload:
      - Copia headers (Authorization: Bearer OPENROUTER_API_KEY)
      - Convierte ChatMessage objects a dict format
      - Includes: model, messages, max_tokens, temperature, stream
   
   b) POST a https://openrouter.ai/api/v1/chat/completions
   
   c) Recibe response:
      {
        "id": "...",
        "created": 1234567890,
        "model": "...",
        "choices": [{
          "message": {"role": "assistant", "content": "Hola, ¿cómo estás?"},
          "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 50}
      }
   
   d) Convierte a ChatResponse (Pydantic model)

5. FastAPI retorna:
   HTTP 200
   Body: ChatResponse JSON

6. Frontend recibe y renderiza
```

**Código referencia**:
```python
# chat.py
@router.post("/completions", response_model=ChatResponse)
async def create_chat_completion(
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    response = await ai_service.chat_completion(request)
    return response

# ai_service.py
async def chat_completion(self, request: ChatRequest) -> ChatResponse:
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    payload = {
        "model": request.model,
        "messages": messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }
    response = await self.client.post("/chat/completions", json=payload)
    data = response.json()
    return ChatResponse(
        id=data.get("id"),
        created=data.get("created"),
        model=data.get("model"),
        choices=data.get("choices"),
    )
```

---

### FLUJO 2: POST /api/v1/tambo/analyze (ANÁLISIS COMPLEJO - EL CORAZÓN DEL APP)

**Archivos**: `app/api/v1/tambo.py`, `app/services/tambo_engine.py`

#### 2.1 Frontend envía datos:

```javascript
POST /api/v1/tambo/analyze
Body: {
  idEstablecimiento: "est-123",
  nombreEstablecimiento: "Tambo La Esperanza",
  periodo: "2024-04",
  lotes: [
    {
      idLote: "lote-1",
      numeroLote: 1,
      fechaProduccion: "2024-04-01",
      producto: "Queso Gouda",
      categoria: "quesos",
      cantidad: 100,  // kg
      unidad: "kg",
      mermas: [
        { descripcion: "Evaporación", cantidad: 2.5, unidad: "kg" },
        { descripcion: "Recortes", cantidad: 1.0, unidad: "kg" }
      ],
      costosDirectos: [
        { concepto: "Mano de obra", monto: 500, moneda: "ARS" }
      ]
    },
    // ... 14 o más lotes
  ]
}
```

#### 2.2 FastAPI recibe y valida (app/api/v1/tambo.py):

```python
@router.post("/analyze", response_model=TamboAnalysisOutput)
async def analyze_production(
    data: TamboAnalysisInput,  # ← Pydantic valida estructura
    db: AsyncSession = Depends(get_db)  # ← Inyecta BD
):
    # Aquí data es 100% válido
    result = await tambo_engine.analyze(data, db)
    
    # Guarda alertas en BD
    for alerta_lote in result.alertas_detectadas:
        alerta = Alerta(
            id_establecimiento=result.idEstablecimiento,
            id_lote=alerta_lote.idLote,
            ...
        )
        db.add(alerta)
    
    await db.commit()
    return result
```

**Validaciones automáticas de Pydantic**:
```python
class TamboAnalysisInput(BaseModel):
    idEstablecimiento: str
    nombreEstablecimiento: str
    periodo: Optional[str] = None
    lotes: List[LoteInput] = Field(..., min_length=15)  # ← Mínimo 15 lotes!
```

Si hay < 15 lotes → error 422 Unprocessable Entity.

#### 2.3 TamboEngine hace TODO el análisis (app/services/tambo_engine.py):

**Función principal**: `async def analyze(data, db)`

```python
async def analyze(data: TamboAnalysisInput, db: AsyncSession) -> TamboAnalysisOutput:
    # PASO 1: Decidir flujo según cantidad de lotes
    if len(data.lotes) >= 15:
        outliers = await seed_category_averages(data, db)  # ← Baseline
    else:
        outliers = await evaluate_single_lote(data, db)    # ← Update

    alertas: list[AlertaLote] = []

    # PASO 2: Si hay outliers, pedir descripción a IA
    if outliers:
        messages = build_prompt(outliers, data)
        if messages:
            raw_response = await call_model(messages)
            alertas = merge_descriptions(raw_response, outliers, data)
    
    return TamboAnalysisOutput(
        idEstablecimiento=data.idEstablecimiento,
        alertas_detectadas=alertas
    )
```

#### 2.3.1 SUBFLUJO A: seed_category_averages (≥15 lotes)

**Objetivo**: Calcular promedios por categoría y detectar outliers.

**Lógica paso a paso**:

```python
async def seed_category_averages(data, db):
    # PASO 1: Agrupar lotes por categoría
    category_totals = defaultdict(lambda: {
        "merma": 0.0,
        "produccion": 0.0,
        "cantidad_lotes": 0
    })
    
    # PASO 2: Iterar lotes, sumar merma y producción por categoría
    for lote in data.lotes:
        # Calcular merma TOTAL de este lote (suma de todas las mermas)
        merma_total = sum(m.cantidad for m in lote.mermas)
        
        # Calcular % de merma relativo a producción
        pct = (merma_total / lote.cantidad) * 100 if lote.cantidad > 0 else 0.0
        
        # Acumular en la categoría
        category_totals[lote.categoria]["merma"] += merma_total
        category_totals[lote.categoria]["produccion"] += lote.cantidad
        category_totals[lote.categoria]["cantidad_lotes"] += 1
    
    # Ejemplo después de iterar 20 lotes (15 quesos, 5 leches):
    # category_totals = {
    #   "quesos": {"merma": 450.0, "produccion": 10000.0, "cantidad_lotes": 15},
    #   "leches": {"merma": 50.0, "produccion": 5000.0, "cantidad_lotes": 5}
    # }
    
    # PASO 3: Guardar/actualizar promedios en BD
    for cat, totals in category_totals.items():
        avg = (totals["merma"] / totals["produccion"]) * 100 if totals["produccion"] > 0 else 0.0
        # avg para quesos = (450 / 10000) * 100 = 4.5%
        
        # Query: ¿existe PromedioCategoria para este establecimiento+categoría?
        stmt = select(PromedioCategoria).where(
            PromedioCategoria.id_establecimiento == data.idEstablecimiento,
            PromedioCategoria.categoria == cat
        )
        result = await db.execute(stmt)
        record = result.scalars().first()
        
        if not record:
            # Crear nuevo
            record = PromedioCategoria(
                id_establecimiento=data.idEstablecimiento,
                categoria=cat,
            )
            db.add(record)
        
        # Actualizar con nuevos promedios
        record.produccion_acumulada = totals["produccion"]
        record.merma_acumulada = totals["merma"]
        record.pct_merma_promedio = avg
        record.cantidad_lotes = totals["cantidad_lotes"]
    
    await db.commit()
    
    # PASO 4: Detectar OUTLIERS
    outliers = []
    for lote in data.lotes:
        merma_total = sum(m.cantidad for m in lote.mermas)
        pct_lote = (merma_total / lote.cantidad) * 100 if lote.cantidad > 0 else 0.0
        avg_pct = category_avg_pct.get(lote.categoria, 0)
        
        if avg_pct == 0:
            continue  # No hay baseline, skip
        
        # ¿Cuánto % supera este lote al promedio?
        pct_over = (pct_lote - avg_pct) / avg_pct * 100
        
        if pct_over <= 0:
            continue  # No es outlier (igual o mejor que promedio)
        
        # Clasificar por nivel de desvío
        if pct_over <= 3:
            nivel = "bajo"
        elif pct_over <= 5:
            nivel = "medio"
        else:
            nivel = "alto"
        
        # Agregar a outliers
        outliers.append({
            "idLote": lote.idLote,
            "numeroLote": lote.numeroLote,
            "producto": lote.producto,
            "categoria": lote.categoria,
            "unidad": lote.unidad,
            "merma_total": round(merma_total, 2),
            "pct_merma_lote": round(pct_lote, 2),
            "promedio_categoria_pct": round(avg_pct, 2),
            "porcentaje_sobre_promedio": round(pct_over, 1),
            "nivel": nivel,
        })
    
    return outliers
```

**Ejemplo numérico**:
```
Lotes:
  - Lote 1: quesos, 100kg, merma 3kg → 3%
  - Lote 2: quesos, 100kg, merma 3.5kg → 3.5%
  - ...
  - Lote 15: quesos, 100kg, merma 10kg → 10% ← OUTLIER!

Promedio quesos = 4.5%
Lote 15 supera promedio = (10 - 4.5) / 4.5 * 100 = 122% sobre promedio → NIVEL "alto"

Resultado outliers = [
  {
    numeroLote: 15,
    pct_merma_lote: 10,
    promedio_categoria_pct: 4.5,
    porcentaje_sobre_promedio: 122,
    nivel: "alto"
  }
]
```

#### 2.3.2 SUBFLUJO B: evaluate_single_lote (< 15 lotes - modo continuo)

**Objetivo**: Evaluar 1 lote contra baseline existente en BD.

```python
async def evaluate_single_lote(data, db):
    lote = data.lotes[0]  # Solo 1 lote
    merma_total = sum(m.cantidad for m in lote.mermas)
    pct_lote = (merma_total / lote.cantidad) * 100 if lote.cantidad > 0 else 0.0
    
    # PASO 1: Obtener baseline de BD para esta categoría
    stmt = select(PromedioCategoria).where(
        PromedioCategoria.id_establecimiento == data.idEstablecimiento,
        PromedioCategoria.categoria == lote.categoria
    )
    result = await db.execute(stmt)
    record = result.scalars().first()
    
    if not record:
        # BD no inicializada, crear registro inicial
        record = PromedioCategoria(
            id_establecimiento=data.idEstablecimiento,
            categoria=lote.categoria,
            produccion_acumulada=lote.cantidad,
            merma_acumulada=merma_total,
            pct_merma_promedio=pct_lote,
            cantidad_lotes=1
        )
        db.add(record)
        await db.commit()
        return []  # No hay baseline, no hay outlier
    
    # PASO 2: Comparar contra baseline
    avg_pct = record.pct_merma_promedio
    outliers = []
    
    if avg_pct > 0:
        pct_over = (pct_lote - avg_pct) / avg_pct * 100
        
        if pct_over > 0:
            nivel = "bajo" if pct_over <= 3 else "medio" if pct_over <= 5 else "alto"
            outliers.append({...})
    
    # PASO 3: Actualizar BD con este nuevo lote
    record.produccion_acumulada += lote.cantidad
    record.merma_acumulada += merma_total
    record.cantidad_lotes += 1
    record.pct_merma_promedio = (record.merma_acumulada / record.produccion_acumulada) * 100
    
    await db.commit()
    return outliers
```

#### 2.3.3 SUBFLUJO C: IA describe outliers

**Si hay outliers detectados**:

```python
# 1. Construir prompt para IA
messages = build_prompt(outliers, data)
# Retorna: [system_message, user_message]

# 2. Enviar a OpenRouter
raw_response = await call_model(messages)

# 3. Parsear JSON de respuesta
descriptions = parse_json(raw_response)
# Ejemplo: {
#   "15": "El lote L15 de quesos presentó una merma de 10kg (10% del volumen)...",
#   "22": "El lote L22 de quesos..."
# }

# 4. Mergear con datos pre-computados
alertas = merge_descriptions(raw_response, outliers, data)
# Retorna: [AlertaLote, AlertaLote, ...]
```

**El PROMPT que envía a IA**:

```python
system_message = """
Eres un analista técnico de producción lechera y quesera.

Los cálculos ya están hechos. Tu única tarea es redactar una descripción 
técnica y objetiva del desvío de merma para cada lote que se te indica.

REGLAS:
1. Responde ÚNICAMENTE con JSON válido (lista de objetos con 'idLote' y 'descripcion')
2. Sin texto adicional, sin markdown, sin explicaciones fuera del JSON
3. Mención todos los números: merma absoluta, %, promedio categoría, desvío, categoría
4. Máximo 2 oraciones. Tono técnico.
5. Comenzar nombrando el lote: "El lote L21 de la categoría leches presentó..."

Formato: [{"idLote": "21", "descripcion": "El lote L21..."}]
"""

user_message = f"""
Establecimiento: '{data.nombreEstablecimiento}' (ID: {data.idEstablecimiento})

Lotes con desvío detectado:
- numeroLote: 15 | Producto: Queso | Categoría: quesos | Merma: 10kg | 
  Merma lote: 10% | Merma promedio: 4.5% | Supera promedio: 122% | Nivel: alto

Generá las descripciones técnicas.
"""
```

**Respuesta esperada de IA**:
```json
[
  {
    "idLote": "15",
    "descripcion": "El lote L15 de la categoría quesos presentó una merma de 10kg (que es el 10% de su volumen total), superando en un 122% el porcentaje promedio de la categoría quesos (que es tan solo 4.5%)."
  }
]
```

#### 2.4 FastAPI guarda en BD

```python
# app/api/v1/tambo.py (dentro de analyze_production)
for alerta_lote in result.alertas_detectadas:
    alerta = Alerta(
        id_establecimiento=result.idEstablecimiento,
        id_lote=alerta_lote.idLote,
        producto=alerta_lote.producto,
        categoria=alerta_lote.categoria,
        nivel=alerta_lote.nivel,
        descripcion=alerta_lote.descripcion,  # ← Description de IA
    )
    db.add(alerta)

await db.commit()
```

**Lo que se guarda en tabla Alerta**:
```
id              | UUID
id_establecimiento | "est-123"
id_lote         | "lote-15"
producto        | "Queso Gouda"
categoria       | "quesos"
nivel           | "alto"
descripcion     | "El lote L15 de la categoría quesos presentó..."
creado_en       | 2024-04-15 10:30:45
visto           | false
```

#### 2.5 FastAPI retorna resultado

```json
{
  "idEstablecimiento": "est-123",
  "alertas_detectadas": [
    {
      "idLote": "lote-15",
      "numeroLote": 15,
      "producto": "Queso Gouda",
      "categoria": "quesos",
      "nivel": "alto",
      "descripcion": "El lote L15 de la categoría quesos presentó..."
    }
  ]
}
```

---

### FLUJO 3: GET /api/v1/tambo/alertas/{idEstablecimiento} (Leer alertas)

**Archivo**: `app/api/v1/tambo.py`

```python
@router.get("/alertas/{idEstablecimiento}", response_model=List[AlertaResponse])
async def get_alertas(
    idEstablecimiento: str,
    rango: int = None,  # Optional: últimos N días
    db: AsyncSession = Depends(get_db)
):
    # Query base
    stmt = select(Alerta).where(
        Alerta.id_establecimiento == idEstablecimiento
    )
    
    # Si rango es 7, solo alertas de últimos 7 días
    if rango is not None:
        fecha_limite = datetime.utcnow() - timedelta(days=rango)
        stmt = stmt.where(Alerta.creado_en >= fecha_limite)
    
    # Ordenar por más reciente primero
    stmt = stmt.order_by(Alerta.creado_en.desc())
    
    result = await db.execute(stmt)
    alertas = result.scalars().all()  # List[Alerta]
    
    # Convertir a AlertaResponse (Pydantic)
    response = [
        AlertaResponse(
            id=a.id,
            idEstablecimiento=a.id_establecimiento,
            idLote=a.id_lote,
            ...
        )
        for a in alertas
    ]
    
    return response
```

**Request/Response ejemplo**:
```
GET /api/v1/tambo/alertas/est-123?rango=30
→ Todas las alertas del último mes

HTTP 200
[
  {
    "id": "alerta-uuid-1",
    "idEstablecimiento": "est-123",
    "idLote": "lote-15",
    "producto": "Queso Gouda",
    "categoria": "quesos",
    "nivel": "alto",
    "descripcion": "El lote L15...",
    "creadoEn": "2024-04-15T10:30:45Z",
    "visto": false
  },
  { ... más alertas ... }
]
```

---

## 🗄️ ESQUEMA DE BASE DE DATOS

### Tabla 1: `alertas`

```sql
CREATE TABLE alertas (
  id              VARCHAR(36) PRIMARY KEY,  -- UUID
  id_establecimiento VARCHAR(255) NOT NULL,  -- indexed for queries
  id_lote         VARCHAR(255) NOT NULL,
  producto        VARCHAR(255) NOT NULL,
  categoria       VARCHAR(50) NOT NULL,    -- 'quesos' o 'leches'
  nivel           VARCHAR(20) NOT NULL,    -- 'bajo', 'medio', 'alto'
  descripcion     TEXT NOT NULL,            -- Texto de IA
  creado_en       DATETIME DEFAULT NOW(),  -- indexed
  visto           BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_alertas_establecimiento_fecha 
  ON alertas(id_establecimiento, creado_en);
```

**Ejemplo de rows**:
```
id: "alert-1"
id_establecimiento: "est-123"
id_lote: "lote-15"
producto: "Queso Gouda"
categoria: "quesos"
nivel: "alto"
descripcion: "El lote L15 de la categoría quesos presentó una merma de 10kg..."
creado_en: "2024-04-15 10:30:45"
visto: false
```

### Tabla 2: `promedios_categoria`

```sql
CREATE TABLE promedios_categoria (
  id              VARCHAR(36) PRIMARY KEY,     -- UUID
  id_establecimiento VARCHAR(255) NOT NULL,    -- indexed
  categoria       VARCHAR(50) NOT NULL,        -- 'quesos' o 'leches'
  produccion_acumulada FLOAT DEFAULT 0.0,      -- kg/litros acumulados
  merma_acumulada FLOAT DEFAULT 0.0,           -- kg/litros acumulados
  pct_merma_promedio FLOAT DEFAULT 0.0,        -- % calculado
  cantidad_lotes  INT DEFAULT 0                -- número de lotes analizados
);
```

**Ejemplo de rows**:
```
id: "prom-1"
id_establecimiento: "est-123"
categoria: "quesos"
produccion_acumulada: 10000.0     -- 10,000 kg de queso
merma_acumulada: 450.0             -- 450 kg de merma
pct_merma_promedio: 4.5            -- 4.5%
cantidad_lotes: 15                 -- basado en 15 lotes
```

**¿Cómo se actualiza?**:
- Primer `/analyze` (≥15 lotes) → **CREA/ACTUALIZA** este registro (baseline)
- Siguientes `/analyze` (1 lote) → **SUMA** los números y recalcula %

```python
# Después de 1er análisis (15 lotes quesos, 10000kg, 450kg merma)
pct_merma_promedio = (450 / 10000) * 100 = 4.5%

# Después de 2do análisis (1 lote queso nuevo, 100kg, 8kg merma)
produccion_acumulada = 10000 + 100 = 10100
merma_acumulada = 450 + 8 = 458
pct_merma_promedio = (458 / 10100) * 100 = 4.53%
```

---

## 📋 ESQUEMAS PYDANTIC (DTOs)

**Archivo**: `app/models/schemas.py`

### Input Schemas (Frontend → Backend)

```python
class MermaInput(BaseModel):
    descripcion: str  # "Evaporación", "Recortes", etc.
    cantidad: float   # kg o litros
    unidad: str       # "kg" o "litros"

class CostoDirectoInput(BaseModel):
    concepto: str     # "Mano de obra", "Energía", etc.
    monto: float      # cantidad en dinero
    moneda: str       # "USD", "EUR", "ARS"

class LoteInput(BaseModel):
    idLote: str
    numeroLote: int
    fechaProduccion: str  # "2024-04-15"
    producto: str
    categoria: str        # "quesos" o "leches" ← MUST be one of these!
    cantidad: float
    unidad: str           # "kg" o "litros"
    mermas: List[MermaInput] = []          # puede estar vacío
    costosDirectos: List[CostoDirectoInput] = []  # puede estar vacío

class ChatRequest(BaseModel):
    model: str = "arcee-ai/trinity-large-preview:free"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(1000, ge=1, le=4096)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    stream: Optional[bool] = False

class TamboAnalysisInput(BaseModel):
    idEstablecimiento: str
    nombreEstablecimiento: str
    periodo: Optional[str] = None
    lotes: List[LoteInput] = Field(..., min_length=15)  # ← AL MENOS 15!
```

### Output Schemas (Backend → Frontend)

```python
class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]      # [{"message": {...}}]
    usage: Optional[Dict[str, Any]]    # {"prompt_tokens": N, ...}

class AlertaLote(BaseModel):
    idLote: str
    numeroLote: Optional[int] = None
    producto: str
    categoria: str
    nivel: str
    descripcion: str

class TamboAnalysisOutput(BaseModel):
    idEstablecimiento: str
    alertas_detectadas: List[AlertaLote]

class AlertaResponse(BaseModel):
    id: str
    idEstablecimiento: str
    idLote: str
    producto: str
    categoria: str
    nivel: str
    descripcion: str
    creadoEn: datetime
    visto: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    message: Optional[str] = None
```

---

## 🔌 DEPENDENCIAS E INYECCIÓN (FastAPI Magic)

**Archivo**: `app/api/dependencies.py`

```python
async def get_ai_service() -> AIService:
    """Dependency: proporciona instancia de AIService"""
    # FastAPI crea/cachea la instancia automáticamente
    return ai_service

# Uso en endpoints:
@router.post("/completions")
async def endpoint(
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service)  # ← Inyección
):
    # ai_service es pasado automáticamente por FastAPI
    response = await ai_service.chat_completion(request)
    return response
```

**Archivo**: `app/database.py`

```python
async def get_db():
    """Dependency: proporciona sesión de BD para cada request"""
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Le da la sesión al endpoint
        finally:
            await session.close()

# Uso:
@router.post("/analyze")
async def endpoint(
    data: TamboAnalysisInput,
    db: AsyncSession = Depends(get_db)  # ← Inyección
):
    # db es una sesión BD activa para este request
    result = await tambo_engine.analyze(data, db)
    return result
```

---

## ⚙️ CONFIGURACIÓN (Variables de Entorno)

**Archivo**: `.env`

```env
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxx...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@localhost/tambo360_db
# O para SQLite:
# DATABASE_URL=sqlite+aiosqlite:///./tambo360.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# App
APP_NAME=Tambo360 IA API
APP_VERSION=1.0.0
DEBUG=true

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Archivo**: `app/config/settings.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FastAPI AI Template"
    app_version: str = "1.0.0"
    openrouter_api_key: str  # ← Requerido, de .env
    database_url: str         # ← Requerido
    api_port: int = 8000
    debug: bool = True
    ...
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Uso**:
```python
from app.config.settings import settings

print(settings.openrouter_api_key)    # acceso a variable
print(settings.api_port)              # 8000
```

---

## 📝 LOGGING

**Archivo**: `app/core/logging.py`

```python
import logging

def setup_logging():
    """Configurar logging global"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def get_logger(name: str):
    """Obtener logger para un módulo"""
    return logging.getLogger(name)

# Uso en endpoints:
from app.core.logging import get_logger
logger = get_logger(__name__)

logger.info(f"Analysis started for establishment {id}")
logger.warning(f"No baseline found")
logger.error(f"OpenRouter API error: {error}")
```

---

## 🚀 PUNTOS DE ENTRADA Y SERVIDOR

**Archivo**: `main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.database import init_db
from app.api.v1 import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager: startup/shutdown"""
    # STARTUP
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()  # Crear tablas si no existen
    yield
    # SHUTDOWN
    logger.info("Shutdown complete")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc"     # ReDoc
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(api_router)  # Incluir /api/v1/...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,      # 0.0.0.0
        port=settings.api_port,      # 8000
        reload=settings.debug        # True en dev
    )
```

**Cómo se inicia**:
```bash
# Terminal
python main.py

# Salida:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Starting Tambo360 IA API v1.0.0
# INFO:     Database initialized
```

**Acceso**:
- Swagger: http://localhost:8000/docs
- API: http://localhost:8000/api/v1/tambo/analyze
- Health: http://localhost:8000/api/v1/health

---

## 🔌 AIService: Cliente HTTP a OpenRouter

**Archivo**: `app/services/ai_service.py`

```python
import httpx
from app.config.settings import settings

class AIService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,  # https://openrouter.ai/api/v1
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/...",
                "X-Title": settings.app_name,
            },
            timeout=60.0
        )

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """POST a /chat/completions"""
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return ChatResponse(
            id=data.get("id"),
            created=data.get("created"),
            model=data.get("model"),
            choices=data.get("choices"),
            usage=data.get("usage")
        )

    async def list_models(self) -> List[ModelInfo]:
        """GET a /models"""
        response = await self.client.get("/models")
        response.raise_for_status()
        
        data = response.json()
        models_data = data.get("data", [])
        
        return [
            ModelInfo(
                id=model.get("id"),
                name=model.get("name"),
                description=model.get("description"),
                pricing=model.get("pricing")
            )
            for model in models_data
        ]

# Singleton
ai_service = AIService()
```

---

## 🎯 RESUMEN: COMPONENTES CRÍTICOS A TRADUCIR

| Componente | Python | TypeScript | Complejidad |
|-----------|--------|-----------|------------|
| **AIService** | `httpx.AsyncClient` | `axios` o `fetch` | ⭐ Baja |
| **TamboEngine** | Funciones puras + SQLAlchemy | Funciones puras + Prisma | ⭐ Baja |
| **Schemas** | Pydantic `BaseModel` | Zod o interfaces | ⭐ Baja |
| **API Routes** | FastAPI decorators | Express `app.post()` | ⭐ Baja |
| **BD Access** | SQLAlchemy ORM | Prisma client | ⭐ Media |
| **Logging** | `logging` module | Winston/Pino | ⭐ Baja |
| **Settings** | Pydantic `BaseSettings` | Zod + dotenv | ⭐ Baja |
| **Async** | `async/await` | `async/await` | ⭐ Igual |

| **Total lineas**: ~500 líneas Python → ~500 líneas TypeScript (similar)|

---

## 📖 TRADUCCIÓN EXACTA: LÍNEA POR LÍNEA

### Ejemplo 1: seed_category_averages Python → TypeScript

**Python original**:
```python
async def seed_category_averages(data: TamboAnalysisInput, db: AsyncSession) -> list[dict]:
    category_totals = defaultdict(lambda: {"merma": 0.0, "produccion": 0.0, "cantidad_lotes": 0})
    lot_merma_pcts = {}
    lot_merma_totals = {}

    for lote in data.lotes:
        merma_total = sum(m.cantidad for m in lote.mermas)
        lot_merma_totals[lote.idLote] = merma_total
        
        if lote.cantidad > 0:
            pct = (merma_total / lote.cantidad) * 100
        else:
            pct = 0.0
            
        lot_merma_pcts[lote.idLote] = pct
        
        category_totals[lote.categoria]["merma"] += merma_total
        category_totals[lote.categoria]["produccion"] += lote.cantidad
        category_totals[lote.categoria]["cantidad_lotes"] += 1
```

**TypeScript traducción**:
```typescript
async function seedCategoryAverages(
  data: TamboAnalysisInput,
  db: PrismaClient
): Promise<Record<string, any>[]> {
  // defaultdict → Map o objeto anidado
  const categoryTotals: Record<string, {merma: number, produccion: number, cantidadLotes: number}> = {};
  const lotMermaPcts: Record<string, number> = {};
  const lotMermaTotals: Record<string, number> = {};

  // for loop → for...of
  for (const lote of data.lotes) {
    // sum(m.cantidad for m in lote.mermas) → reduce
    const mermaTotal = lote.mermas.reduce((sum, m) => sum + m.cantidad, 0);
    lotMermaTotals[lote.idLote] = mermaTotal;
    
    // if/else idéntico
    const pct = lote.cantidad > 0 ? (mermaTotal / lote.cantidad) * 100 : 0.0;
    lotMermaPcts[lote.idLote] = pct;
    
    // Inicializar categoría si no existe (replace defaultdict)
    if (!categoryTotals[lote.categoria]) {
      categoryTotals[lote.categoria] = { merma: 0.0, produccion: 0.0, cantidadLotes: 0 };
    }
    
    categoryTotals[lote.categoria].merma += mermaTotal;
    categoryTotals[lote.categoria].produccion += lote.cantidad;
    categoryTotals[lote.categoria].cantidadLotes += 1;
  }
```

**Cambios clave**:
- `defaultdict(lambda: {...})` → inicializar `if (!categoryTotals[key])`
- `sum(m.cantidad for m in lista)` → `lista.reduce((sum, m) => sum + m.cantidad, 0)`
- `for lote in data.lotes:` → `for (const lote of data.lotes)`
- Tipos TypeScript: `Record<string, any>` en lugar de `dict`

### Ejemplo 2: Queries de BD Python → TypeScript

**Python (SQLAlchemy)**:
```python
stmt = select(PromedioCategoria).where(
    PromedioCategoria.id_establecimiento == data.idEstablecimiento,
    PromedioCategoria.categoria == cat
)
result = await db.execute(stmt)
record = result.scalars().first()

if not record:
    record = PromedioCategoria(
        id_establecimiento=data.idEstablecimiento,
        categoria=cat,
    )
    db.add(record)

record.pct_merma_promedio = avg
await db.commit()
```

**TypeScript (Prisma)**:
```typescript
let record = await db.promedioCategoria.findFirst({
  where: {
    idEstablecimiento: data.idEstablecimiento,
    categoria: cat,
  },
});

if (!record) {
  record = await db.promedioCategoria.create({
    data: {
      idEstablecimiento: data.idEstablecimiento,
      categoria: cat,
    },
  });
}

await db.promedioCategoria.update({
  where: { id: record.id },
  data: { pctMermaPromedio: avg },
});
```

**Cambios clave**:
- `select(Model).where(...)` → `db.tableName.findFirst({ where: {...} })`
- `result.scalars().first()` → resultado directo
- `db.add()` + `commit()` → `db.create()` o `db.update()` automáticamente
- Nombres: snake_case (Python/SQL) → camelCase (TypeScript/Prisma)

### Ejemplo 3: Endpoints FastAPI → Express

**FastAPI**:
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/completions", response_model=ChatResponse)
async def create_chat_completion(
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    response = await ai_service.chat_completion(request)
    return response
```

**Express/TypeScript**:
```typescript
import { Router } from 'express';
import { aiService } from '../services/aiService';

const router = Router();

router.post('/completions', async (req, res) => {
  try {
    // Validar con Zod (reemplaza Pydantic)
    const request = ChatRequestSchema.parse(req.body);
    const response = await aiService.chatCompletion(request);
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
```

**Cambios clave**:
- `@router.post()` → `router.post()`
- `Depends(get_ai_service)` → pasarlo a través de middleware o contexto
- Validación: `response_model` (automática en FastAPI) → `Schema.parse()` (manual con Zod)
- Error handling: HTTPException → `res.status(500).json()`

### Ejemplo 4: Inicialización y lifespan

**FastAPI**:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("Starting app")
    await init_db()
    yield
    # SHUTDOWN
    logger.info("Shutting down")

app = FastAPI(lifespan=lifespan)
```

**Express**:
```typescript
// Startup
logger.info("Starting app");
await initDb();

const server = app.listen(port, () => {
  logger.info(`Server running on port ${port}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info("SIGTERM signal received: closing HTTP server");
  server.close(() => {
    logger.info("HTTP server closed");
    process.exit(0);
  });
});
```

**Cambios clave**:
- `asynccontextmanager` + lifespan → startup code + shutdown listeners
- `app.listen()` → start server explícitamente
- Graceful shutdown con `process.on('SIGTERM')`

---

## 🎯 CHECKLIST DE TRADUCCIÓN PASO A PASO

### Fase 1: Preparación Inicial

- [ ] Crear carpeta `tambo360-ia-ts` en mismo nivel que Python
- [ ] `npm init -y`
- [ ] Instalar todas las dependencias (ver sección Dependencias)
- [ ] Crear `tsconfig.json` con strict mode
- [ ] Crear `.env` copiando del Python (cambiar DATABASE_URL si es necesario)
- [ ] Crear carpeta `src/` con estructura:
  ```
  src/
    ├── index.ts
    ├── config/
    │   └── settings.ts
    ├── services/
    │   ├── aiService.ts
    │   └── tamboEngine.ts
    ├── routes/
    │   ├── index.ts
    │   ├── chat.ts
    │   └── tambo.ts
    ├── types/
    │   └── schemas.ts
    ├── db/
    │   └── prisma.ts (client)
    └── utils/
        └── logger.ts
  ```

### Fase 2: Base de datos (Prisma)

- [ ] `npx prisma init`
- [ ] Editar `prisma/.env` con DATABASE_URL
- [ ] Crear `schema.prisma` con modelos Alerta y PromedioCategoria
- [ ] `npx prisma db push` (si BD existe con tablas)
- [ ] O: `npx prisma migrate dev --name init` (si BD vacía)
- [ ] Verificar BD tiene datos después de migración
- [ ] `npx prisma generate` (generar tipos TypeScript)
- [ ] Crear `src/db/prisma.ts`:
  ```typescript
  import { PrismaClient } from '@prisma/client';
  export const db = new PrismaClient();
  ```

### Fase 3: Configuración y Schemas

- [ ] Copiar `.env` variables
- [ ] Crear `src/config/settings.ts` con Zod parsing
- [ ] Crear `src/types/schemas.ts` con Zod schemas para:
  - [ ] ChatMessage, ChatRequest, ChatResponse
  - [ ] MermaInput, CostoDirectoInput, LoteInput
  - [ ] TamboAnalysisInput, TamboAnalysisOutput
  - [ ] AlertaLote, AlertaResponse
- [ ] Generar tipos TypeScript: `export type ChatRequest = z.infer<typeof ChatRequestSchema>`

### Fase 4: Servicios

- [ ] Crear `src/utils/logger.ts` (Winston o Pino)
- [ ] Crear `src/services/aiService.ts`:
  - [ ] Constructor: crear axios client con headers OpenRouter
  - [ ] `chatCompletion(request): Promise<ChatResponse>`
  - [ ] `listModels(): Promise<ModelInfo[]>`
  - [ ] Error handling
  - [ ] Logs en lugares críticos

- [ ] Crear `src/services/tamboEngine.ts`:
  - [ ] `seedCategoryAverages(data, db): Promise<any[]>` - traducción línea x línea
  - [ ] `evaluateSingleLote(data, db): Promise<any[]>` - traducción línea x línea
  - [ ] `buildPrompt(outliers, data): ChatMessage[]` - traducción del prompt
  - [ ] `callModel(messages): Promise<string>` - llamada a IA
  - [ ] `mergeDescriptions(raw, outliers, data): AlertaLote[]` - parsear JSON
  - [ ] `analyze(data, db): Promise<TamboAnalysisOutput>` - orquestador
  - [ ] **CRÍTICO**: Escribir tests que comparen números Python vs TypeScript

### Fase 5: Rutas API

- [ ] Crear `src/routes/chat.ts`:
  - [ ] `POST /chat/completions` → llama `aiService.chatCompletion()`
  - [ ] `GET /chat/models` → llama `aiService.listModels()`
  - [ ] Validación con Zod
  - [ ] Error handling (500)

- [ ] Crear `src/routes/tambo.ts`:
  - [ ] `POST /tambo/analyze` → llama `tamboEngine.analyze()`
  - [ ] `GET /tambo/alertas/:idEstablecimiento` → query Prisma
  - [ ] `GET /tambo/alertas/:idEstablecimiento/ultimas` → query Prisma limit 2
  - [ ] `PUT /tambo/alertas/:idAlerta/visto` → update Prisma
  - [ ] Validación con Zod
  - [ ] Error handling (404, 500)

- [ ] Crear `src/routes/health.ts`:
  - [ ] `GET /health` → retorna HealthResponse

- [ ] Crear `src/routes/index.ts` → combinar todas las rutas

### Fase 6: Aplicación principal

- [ ] Crear `src/index.ts`:
  - [ ] Importar express, rutas, configuración
  - [ ] Crear `app = express()`
  - [ ] CORS middleware
  - [ ] JSON body parser middleware
  - [ ] Registrar rutas: `app.use('/api/v1', routesV1)`
  - [ ] Error handler middleware
  - [ ] Startup: `await initDb()` (Prisma)
  - [ ] Listen: `app.listen(PORT)`
  - [ ] Graceful shutdown

- [ ] Crear `package.json` scripts:
  ```json
  {
    "scripts": {
      "dev": "ts-node src/index.ts",
      "build": "tsc",
      "start": "node dist/index.js",
      "test": "jest",
      "prisma:migrate": "npx prisma migrate dev"
    }
  }
  ```

### Fase 7: Testing

- [ ] Instalar `jest` + `ts-jest`
- [ ] Crear `jest.config.js`
- [ ] Tests de TamboEngine:
  - [ ] 10 casos: Python input → Python output
  - [ ] 10 casos: TypeScript input → TypeScript output
  - [ ] Validar: números idénticos (abs difference < 0.01)
  - [ ] Test edge cases: división por cero, arrays vacíos
- [ ] Tests de endpoints (si quieres):
  - [ ] Mock aiService
  - [ ] Mock Prisma
  - [ ] Validar status codes y respuestas

### Fase 8: Validación Final

- [ ] Levantar backend TypeScript
- [ ] Levantar backend Python (en otro puerto)
- [ ] Enviar mismo request a ambos
- [ ] Comparar respuestas JSON (números deben ser iguales)
- [ ] Verificar BD: datos guardados correctamente
- [ ] Verificar logs: mensajes aparecen correctamente
- [ ] Verificar CORS: frontend puede conectar

### Fase 9: Cutover

- [ ] Parar backend Python
- [ ] Apuntar frontend a backend TypeScript
- [ ] Monitorear logs por 24 horas
- [ ] Validar: usuarios pueden usar app sin errores
- [ ] Borrar código Python (o archivar en rama git)

---

## 🔍 VALIDACIONES CRÍTICAS DURANTE TRADUCCIÓN

### Validación 1: Números exactos TamboEngine

**Cómo hacer**:
1. Tomar 5-10 casos de prueba (input JSON)
2. Ejecutar en Python, guardar output
3. Ejecutar en TypeScript con mismo input
4. Comparar números:

```python
# Python output
{
  "porcentaje_sobre_promedio": 122.5,
  "pct_merma_lote": 10.2
}
```

```typescript
// TypeScript output
{
  "porcentaje_sobre_promedio": 122.5,  // ← DEBE SER EXACTO
  "pct_merma_lote": 10.2               // ← DEBE SER EXACTO
}
```

**Riesgos**:
- Redondeo diferente (usar `.toFixed(2)` en ambos lados)
- Division order (calcular en mismo orden)
- Float precision (cuidado con sumas largas)

### Validación 2: BD queries

**Cómo hacer**:
1. Ejecutar `/analyze` en Python, verificar registros en tabla Alerta
2. Ejecutar `/analyze` en TypeScript con MISMO data, verificar registros
3. Comparar:
   - Número de alertas
   - Contenido de campos
   - Timestamps (deben ser UTC)

### Validación 3: OpenRouter headers

**Cómo hacer**:
1. Activar verbose logging en httpx (Python) y axios (TypeScript)
2. Enviar request a OpenRouter desde ambos
3. Comparar headers enviados:
   - Authorization
   - Content-Type
   - HTTP-Referer
   - X-Title

### Validación 4: Errores y edge cases

**Casos a testear**:
- [ ] Entrada vacía: `lotes: []`
- [ ] Categoría desconocida: `categoria: "otros"`
- [ ] Merma negativa: `cantidad: -5`
- [ ] División por cero: `produccion: 0`
- [ ] OpenRouter timeout: esperar 60s
- [ ] BD desconectada: error handling

---

## 📞 TEMPLATE PARA CHATGPT

Cuando pases esto a ChatGPT, dale este contexto al principio:

```
CONTEXTO:
Estoy migrando un backend FastAPI (Python) a Express (TypeScript).

El backend es relativamente simple:
- ~500 líneas de código Python
- 2 endpoints principales: POST /analyze (análisis complejo) y GET /alertas (lectura)
- Usa OpenRouter API para llamadas a IA
- SQLite/PostgreSQL con 2 tablas: Alerta y PromedioCategoria

LÓGICA CENTRAL (TamboEngine):
1. Recibe lista de "lotes" (>=15 o 1)
2. Calcula promedios de "merma" por categoría
3. Identifica "outliers" (lotes que desvían del promedio)
4. Para cada outlier, solicita descripción a IA (OpenRouter)
5. Guarda alertas en BD

TAREA:
Voy a proporcionar el código Python línea por línea. Necesito que me guíes en traducir a TypeScript manteniendo EXACTITUD EN NÚMEROS (sin redondeos diferentes).

Puntos críticos:
- Las matemáticas deben ser idénticas
- Las queries de BD cambiarán de SQLAlchemy → Prisma
- Los endpoints cambiarán de FastAPI decorators → Express routes
- Pydantic validación → Zod validación

Estoy en la Fase [X]. Mi siguiente tarea es [TAREA_ESPECÍFICA].
```

---

## 🎉 FINAL

Has llegado al final de este documento. Este IS tu mapa completo:
- Entiende CÓMO funciona el backend actual
- Entiende QUÉ traducir
- Entiende CÓMO traducir
- Entiende QUÉ validar

**Próximo paso**: Pasale este documento COMPLETO a ChatGPT y empieza por la Fase 1.

**Tiempo estimado total**: 15-20 horas de trabajo (depende de tu velocidad y familiaridad con TypeScript/Express)

**Success metrics**:
- Mismos números en outputs
- Mismos datos en BD
- Mismo comportamiento de API
- Cero diferencias funcionales

---

**Fin de guía. Pasa este archivo a ChatGPT y ¡comienza la migración!**
- GET a `https://openrouter.ai/api/v1/models`
- Manejo de errores

**Traducción TypeScript**:
