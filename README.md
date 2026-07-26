# Consejero de Apoyo Emocional — Agente conversacional con LangGraph

> ### ⚠️ Proyecto educativo
>
> Este repositorio existe para **aprender a construir agentes conversacionales con LLMs**:
> LangGraph, OpenRouter, FastAPI y React. Es material didáctico.
>
> **No es un servicio de salud mental, no sustituye atención profesional y no debe desplegarse
> como una herramienta de apoyo emocional real.** Si necesitas ayuda, contacta los servicios de
> salud de tu país.

Un agente que escucha, responde con empatía apoyándose en enfoques de psicología con evidencia
(TCC, ACT, psicología positiva) y refuerza sus mensajes con **citas célebres reales y
correctamente atribuidas**, seleccionadas de un banco curado — nunca generadas por el modelo.

---

## Qué se aprende aquí

| Concepto | Dónde mirarlo |
|---|---|
| Estado compartido y **reducers** (`add_messages`) | [`backend/app/graph/state.py`](backend/app/graph/state.py) |
| **Ruteo condicional** con `add_conditional_edges` | [`backend/app/graph/workflow.py`](backend/app/graph/workflow.py) |
| **Memoria por conversación** con checkpointer y `thread_id` | [`backend/app/graph/workflow.py`](backend/app/graph/workflow.py) |
| Nodos, entradas y salidas parciales del estado | [`backend/app/graph/nodes.py`](backend/app/graph/nodes.py) |
| Streaming SSE de LangGraph a FastAPI a React | [`backend/app/main.py`](backend/app/main.py) · [`frontend/src/services/api.js`](frontend/src/services/api.js) |
| Cómo **probar un grafo** de LangGraph | [`backend/tests/test_graph.py`](backend/tests/test_graph.py) |
| Evitar alucinaciones sin RAG: banco curado como input | [`backend/app/data/quotes.json`](backend/app/data/quotes.json) |

---

## Arquitectura

```
[ React (Vite) ]
      │  POST /api/chat  · SSE
      ▼
[ FastAPI ]
      │  thread_id + mensaje nuevo
      ▼
[ Grafo de LangGraph ]

      safety_check
           │
    ┌──────┴───────┐
  riesgo        sin riesgo
    │               │
crisis_response  summarize_history
    │               │
    │          retrieve_quote
    │               │
    │           counselor
    └───────┬───────┘
           END
```

**Los nodos**

| Nodo | Qué hace |
|---|---|
| `safety_check` | Clasifica el mensaje entrante. Si detecta riesgo, desvía a la rama de crisis, que tiene prioridad sobre todo lo demás |
| `crisis_response` | Contención inmediata más los recursos configurados. Sin consejos genéricos y sin cita |
| `summarize_history` | Comprime el historial si supera el umbral. Por debajo, pasa sin llamar al modelo |
| `retrieve_quote` | Selecciona una cita del banco curado por tema. Puede devolver `None`, y eso es válido |
| `counselor` | Llama al LLM con el prompt clínico y la cita como **dato de entrada** |

**Cómo se mantiene el contexto.** El frontend envía solo el mensaje nuevo. LangGraph recupera el
estado guardado para ese `thread_id`, le aplica la entrada con el reducer `add_messages`, ejecuta
el grafo y vuelve a guardar. El historial nunca viaja por la red: lo reconstruye el checkpointer.

---

## Puesta en marcha

**Requisitos:** Python 3.10 o superior · Node.js 18 o superior · una clave de
[OpenRouter](https://openrouter.ai/keys)

### 1. Backend

<details open>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# edita .env y pon tu OPENROUTER_API_KEY
uvicorn app.main:app --reload --port 8000
```

Si `Activate.ps1` da error de política de ejecución:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edita .env y pon tu OPENROUTER_API_KEY
uvicorn app.main:app --reload --port 8000
```

</details>

> **Importante:** `uvicorn` debe lanzarse **desde `backend/`**. `main.py` abre los archivos de
> datos con rutas relativas al directorio de trabajo.

### 2. Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre **http://localhost:5173**

### 3. Comprobar que arrancó bien

En los logs del backend deben aparecer:

| Línea | Significa |
|---|---|
| `[CAM-01 ÉXITO]` | El modelo configurado existe en el catálogo de OpenRouter |
| `[CAM-02 ADVERTENCIA]` | Los recursos de crisis están sin configurar. **Es correcto**: el repositorio se distribuye así a propósito |

---

## Configuración

`backend/.env` (parte de `backend/.env.example`):

| Variable | Descripción |
|---|---|
| `OPENROUTER_API_KEY` | Tu clave de OpenRouter |
| `MODEL_ID` | Slug del modelo. Por defecto uno con precio `0` |
| `ALLOWED_ORIGINS` | Orígenes CORS **separados por comas**. Sin corchetes ni comillas |
| `HOST` · `PORT` | Dirección del servidor |

> `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173` ✅
> `ALLOWED_ORIGINS=["http://localhost:5173"]` ❌ — el formato JSON produce orígenes inválidos y
> CORS falla **en silencio**: el navegador bloquea la respuesta sin que el backend registre nada.

**El `.env` nunca se sube al repositorio.** Está en `.gitignore`; solo se versiona `.env.example`.

### Recursos de crisis — léelo antes de desplegar nada

`backend/app/data/crisis_resources.json` se distribuye **sin configurar**, a propósito. Este
proyecto no incluye números de líneas de ayuda porque un teléfono inventado o desactualizado,
entregado a alguien en crisis, es el peor resultado posible.

Para configurarlo, completa el archivo con fuentes **oficiales de tu país** y pon
`"configured": true`:

```json
{
  "configured": true,
  "regions": {
    "default": {
      "label": "Líneas de atención oficiales",
      "message": "Si estás en crisis, contacta estos servicios:",
      "resources": [
        {
          "name": "",
          "phone": "",
          "hours": "",
          "source_url": "",
          "verified_at": "AAAA-MM-DD"
        }
      ]
    }
  }
}
```

Sin configurar, la rama de crisis responde con contención y remite a los servicios de emergencia
locales, sin dar ningún número.

---

## Pruebas

Desde `backend/`, con el entorno virtual activo:

```bash
pytest tests/ -v
```

Cuatro pruebas sobre el grafo, con el LLM sustituido por un doble: verifican **enrutamiento**, no
la salida del modelo.

| Prueba | Qué garantiza |
|---|---|
| `test_crisis_tiene_prioridad` | La rama de crisis se activa y **no** pasa por `retrieve_quote` ni `counselor` |
| `test_ruta_normal` | El camino sin riesgo recorre `retrieve_quote` y `counselor` |
| `test_sin_cita_disponible` | Sin cita relevante, el grafo completa igual |
| `test_contexto_persiste` | Dos turnos con el mismo `thread_id` comparten historial |

---

## El banco de citas

20 citas, todas con autor y obra verificados. El campo `verified` no es decorativo: **ante
cualquier duda sobre la atribución, la cita se excluye.** Muchas frases de circulación masiva
están mal atribuidas.

```json
{
  "id": "frankl-001",
  "text": "…",
  "author": "Viktor E. Frankl",
  "source": "El hombre en busca de sentido",
  "themes": ["sentido", "adversidad", "resiliencia"],
  "verified": true
}
```

El modelo **selecciona** de este archivo; nunca genera una cita. Es la forma más barata de evitar
alucinaciones en un dominio donde inventar una atribución sería inaceptable.

---

## Qué NO es esto

El código está lleno de comentarios marcados con `DEMO:`. Cada uno señala un atajo deliberado y
qué haría falta en un despliegue real:

| Atajo | Dónde | Qué haría falta |
|---|---|---|
| Estado en memoria del proceso | `graph/workflow.py` | Un checkpointer persistente |
| `thread_id` aceptado del cliente sin autenticar | `main.py` | Sesión firmada por el servidor. **Tal cual, quien conozca un `thread_id` lee esa conversación** |
| Detección de crisis por palabras clave | `graph/nodes.py` | Un clasificador evaluado, con falsos negativos y positivos medidos |
| Endpoint sin límite de tasa ni de tamaño | `main.py` | Cuotas y validación de entrada |
| Detener la respuesta solo corta la escucha | `App.jsx` | Propagar la desconexión hasta el nodo del grafo |

Ninguno es un descuido. Están así para que el código se lea, y marcados para que nadie los
confunda con una implementación lista para producción.

---

## Estructura

```
backend/
  app/
    main.py              Endpoints, CORS, validación del modelo al arranque
    config.py            Variables de entorno
    graph/
      state.py           AgentState y sus reducers
      nodes.py           Los cinco nodos
      workflow.py        Construcción del grafo y checkpointer
      prompts.py         Prompt del consejero
    data/
      quotes.json              Banco curado de citas
      crisis_resources.json    Recursos de crisis (sin configurar)
    schemas/chat.py      Modelos Pydantic
  tests/test_graph.py    Pruebas de enrutamiento
frontend/
  src/
    components/          Chat, cabecera, tarjeta de crisis, aviso, selector de idioma
    i18n/                Diccionarios ES / EN y su contexto
    services/api.js      Cliente SSE con cancelación
```

---

## Stack

| Capa | Tecnología |
|---|---|
| Orquestación del agente | LangGraph 0.2.56 |
| Backend | FastAPI 0.115.6 · Uvicorn · Pydantic 2 |
| Proveedor de modelo | OpenRouter (API compatible con OpenAI) |
| Frontend | React 18 · Vite 6 · sin librería de i18n |

Las versiones de Python están fijadas con `==` en `requirements.txt`: las firmas de API de
LangGraph se verificaron contra esa versión concreta.
