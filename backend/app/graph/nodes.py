import json
import os
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.state import AgentState
from app.graph.prompts import COUNSELOR_SYSTEM_PROMPT, SUMMARIZE_SYSTEM_PROMPT

# Cargar banco de citas
QUOTES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "quotes.json")
try:
    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        QUOTES_DB = json.load(f)
except Exception:
    QUOTES_DB = []

# Cargar recursos de crisis (CAM-02)
CRISIS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "crisis_resources.json")
try:
    with open(CRISIS_FILE, "r", encoding="utf-8") as f:
        CRISIS_DB = json.load(f)
except Exception:
    CRISIS_DB = {"configured": False, "regions": {"default": {"message": "Este proyecto es una demostración educativa."}}}

def get_llm():
    """Instancia el modelo mediante ChatOpenAI hacia OpenRouter."""
    return ChatOpenAI(
        model=settings.MODEL_ID,
        openai_api_key=settings.OPENROUTER_API_KEY or "dummy-key-for-test",
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        default_headers={
            "HTTP-Referer": "https://github.com/educational/emotional-support-demo",
            "X-Title": "Emotional Support Agent Demo"
        }
    )

def safety_check(state: AgentState) -> Dict[str, Any]:
    # DEMO: Clasificación en safety_check por coincidencia de palabras clave: insuficiente para uso real, produce falsos negativos y falsos positivos.
    last_user_msg = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_msg = msg.content.lower()
            break
            
    crisis_keywords = [
        "suicid", "autolesion", "matarme", "hacerme daño", "quitarme la vida",
        "terminar con todo", "no quiero vivir", "hacerme dano", "cortarme"
    ]
    
    is_crisis = any(kw in last_user_msg for kw in crisis_keywords)
    return {"is_crisis": is_crisis}

def crisis_response(state: AgentState) -> Dict[str, Any]:
    """Respuesta inmediata de apoyo y contención ante detección de crisis (CAM-02)."""
    default_info = CRISIS_DB.get("regions", {}).get("default", {})
    message = (
        "Siento mucho que estés pasando por un momento tan doloroso y difícil. "
        "Tu vida y tu bienestar son profundamente importantes. "
        f"\n\n{default_info.get('message', '')}"
    )
    return {
        "messages": [AIMessage(content=message)],
        "is_crisis": True,
        "selected_quote": None
    }

def summarize_history(state: AgentState) -> Dict[str, Any]:
    """Compresión condicional del historial si supera el umbral nombrado (CAM-03)."""
    messages = state.get("messages", [])
    if len(messages) <= settings.MAX_HISTORY_MESSAGES:
        # LangGraph rechaza un nodo que devuelve {}: exige actualizar al menos una clave del
        # estado. Se reescribe summary con su propio valor: paso sin efecto.
        return {"summary": state.get("summary", "")}
        
    summary = state.get("summary", "")
    llm = get_llm()
    prompt = f"Resumen actual: {summary}\n\nMensajes recientes a condensar:\n"
    for m in messages[:-4]:
        role = "Usuario" if isinstance(m, HumanMessage) else "Consejero"
        prompt += f"{role}: {m.content}\n"
        
    try:
        res = llm.invoke([SystemMessage(content=SUMMARIZE_SYSTEM_PROMPT), HumanMessage(content=prompt)])
        new_summary = res.content
    except Exception:
        new_summary = summary
        
    return {"summary": new_summary}

def retrieve_quote(state: AgentState) -> Dict[str, Any]:
    """Selección de cita del banco curado según el tema detectado (CAM-04)."""
    last_user_msg = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_msg = msg.content.lower()
            break
            
    # Mapeo simple de temas
    selected = None
    for quote in QUOTES_DB:
        for theme in quote.get("themes", []):
            if theme in last_user_msg:
                selected = quote
                break
        if selected:
            break
            
    # CAM-04: retrieve_quote puede devolver None (es un resultado válido, no un error)
    return {"selected_quote": selected}

def counselor(state: AgentState) -> Dict[str, Any]:
    """Nodo principal del LLM para el consejero empático (CAM-04)."""
    quote = state.get("selected_quote")
    summary = state.get("summary", "Sin historial previo condensado.")
    
    if quote:
        quote_context = f'"{quote["text"]}" — {quote["author"]} ({quote["source"]})'
    else:
        # CAM-04: Ausencia explícita de cita
        quote_context = "SIN CITA ASIGNADA. Responde de forma empática sin incluir ninguna cita célebre."
        
    formatted_system = COUNSELOR_SYSTEM_PROMPT.format(
        summary_context=summary,
        quote_context=quote_context
    )
    
    llm = get_llm()
    messages_to_send = [SystemMessage(content=formatted_system)] + state.get("messages", [])
    
    res = llm.invoke(messages_to_send)
    return {"messages": [AIMessage(content=res.content)]}
