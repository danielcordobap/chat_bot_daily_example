from typing import Annotated, Optional, Dict, Any, List
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Historial de mensajes acumulado por LangGraph
    messages: Annotated[List[AnyMessage], add_messages]
    
    # Flag de detección de crisis por safety_check
    is_crisis: bool
    
    # CAM-04: Campo opcional para transportar la cita célebre seleccionada. None si no hay cita disponible.
    selected_quote: Optional[Dict[str, Any]]
    
    # Resumen acumulado de conversaciones previas para no exceder la ventana de contexto
    summary: str
