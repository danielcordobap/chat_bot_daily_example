import json
import logging
import uuid
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, ThreadCreateResponse
from app.graph.workflow import app_graph

# Configurar logging estructurado (NUNCA registra contenido de mensajes del usuario)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("emotional_support_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # CAM-01: Validación al arranque de FastAPI contra el catálogo de OpenRouter
    logger.info(f"Validando MODEL_ID: '{settings.MODEL_ID}' contra el catálogo de OpenRouter...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            if resp.status_code == 200:
                models_data = resp.json().get("data", [])
                catalog = {m.get("id"): m for m in models_data}
                entry = catalog.get(settings.MODEL_ID)

                if entry is None:
                    logger.error(
                        f"[CAM-01 ERROR] El MODEL_ID configurado '{settings.MODEL_ID}' NO está disponible en OpenRouter catalog. "
                        f"Fallbacks válidos con precio 0: {settings.VERIFIED_FREE_FALLBACKS}"
                    )
                else:
                    pricing = entry.get("pricing") or {}
                    try:
                        prompt_price = float(pricing.get("prompt") or 0)
                        completion_price = float(pricing.get("completion") or 0)
                    except (TypeError, ValueError):
                        # Degradación: precio ilegible. Se avisa, no se bloquea el arranque.
                        prompt_price = completion_price = -1.0

                    if prompt_price < 0 or completion_price < 0:
                        logger.warning(
                            f"[CAM-01 WARNING] No se pudo determinar el precio de '{settings.MODEL_ID}'. "
                            f"Verifica manualmente que sea gratuito antes de usarlo."
                        )
                    elif prompt_price > 0 or completion_price > 0:
                        logger.warning(
                            f"[CAM-01 WARNING] El MODEL_ID '{settings.MODEL_ID}' NO es gratuito "
                            f"(prompt={prompt_price}, completion={completion_price}). Su uso genera cobros "
                            f"en la cuenta de OpenRouter configurada. Modelos verificados sin coste: "
                            f"{settings.VERIFIED_FREE_FALLBACKS}"
                        )
                    else:
                        logger.info(f"[CAM-01 ÉXITO] El MODEL_ID '{settings.MODEL_ID}' está verificado en OpenRouter con precio 0.")
            else:
                logger.warning(f"[CAM-01 WARNING] Respuesta HTTP {resp.status_code} al consultar catálogo de OpenRouter.")
    except Exception as e:
        logger.error(f"[CAM-01 ERROR] No se pudo verificar catálogo de OpenRouter al arranque: {str(e)}")

    # CAM-02: Advertencia de recursos de crisis sin configurar
    try:
        crisis_path = "app/data/crisis_resources.json"
        with open(crisis_path, "r", encoding="utf-8") as f:
            crisis_data = json.load(f)
            if not crisis_data.get("configured", False):
                logger.warning(
                    f"[CAM-02 ADVERTENCIA] Recursos de crisis en '{crisis_path}' están sin configurar (configured: false). "
                    "Se utilizará el mensaje predeterminado de demostración."
                )
    except Exception as e:
        logger.warning(f"[CAM-02 ADVERTENCIA] No se pudo leer crisis_resources.json: {e}")

    # Orígenes CORS efectivos: hace visible una configuración inválida en el arranque.
    logger.info(f"[CORS] Orígenes permitidos: {settings.allowed_origins_list}")

    yield
    logger.info("Apagando servicio backend.")

app = FastAPI(
    title="Emotional Support Agent API",
    version="1.0.0",
    description="Backend para aplicación educativa de apoyo emocional con LangGraph y OpenRouter",
    lifespan=lifespan
)

# DEMO: Registro de rutas en main.py: Sin límite de tasa ni de tamaño de entrada: el endpoint es un proxy abierto al modelo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "model": settings.MODEL_ID,
        "app_name": "Emotional Support Demo"
    }

@app.post("/api/threads", response_model=ThreadCreateResponse)
async def create_thread():
    session_id = str(uuid.uuid4())
    logger.info(f"Nuevo hilo creado: session_id={session_id}")
    return ThreadCreateResponse(session_id=session_id, created_at="2026-07-25T00:00:00Z")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # DEMO: Recepción de thread_id en el endpoint: Identificador aceptado del cliente sin autenticación: quien conozca un thread_id lee esa conversación.
    logger.info(f"Procesando solicitud de chat. session_id={request.session_id}, length={len(request.message)}")
    
    config = {"configurable": {"thread_id": request.session_id}}
    input_state = {"messages": [HumanMessage(content=request.message)]}
    
    async def generate_sse_stream() -> AsyncGenerator[str, None]:
        try:
            # Ejecutar el grafo con LangGraph astream
            async for event in app_graph.astream(input_state, config=config, stream_mode="values"):
                messages = event.get("messages", [])
                if messages and hasattr(messages[-1], "content"):
                    last_msg = messages[-1]
                    if hasattr(last_msg, "type") and last_msg.type == "ai":
                        is_crisis = event.get("is_crisis", False)
                        quote = event.get("selected_quote")
                        
                        chunk_payload = {
                            "session_id": request.session_id,
                            "content": last_msg.content,
                            "is_crisis": is_crisis,
                            "quote": quote
                        }
                        yield f"data: {json.dumps(chunk_payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Error en streaming de respuesta: {str(e)}")
            err_payload = {"error": "Error interno del servicio al procesar la solicitud."}
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(generate_sse_stream(), media_type="text/event-stream")
