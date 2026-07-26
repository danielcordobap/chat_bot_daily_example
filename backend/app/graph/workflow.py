from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import AgentState
from app.graph.nodes import safety_check, crisis_response, summarize_history, retrieve_quote, counselor

def route_safety(state: AgentState) -> str:
    """Función condicional para evaluar si redirigir a crisis o al flujo normal."""
    if state.get("is_crisis", False):
        return "crisis_response"
    return "summarize_history"

def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Agregar Nodos
    workflow.add_node("safety_check", safety_check)
    workflow.add_node("crisis_response", crisis_response)
    workflow.add_node("summarize_history", summarize_history)
    workflow.add_node("retrieve_quote", retrieve_quote)
    workflow.add_node("counselor", counselor)
    
    # Punto de entrada
    workflow.set_entry_point("safety_check")
    
    # CAM-03: Aristas y ruteo condicional desde safety_check
    workflow.add_conditional_edges(
        "safety_check",
        route_safety,
        {
            "crisis_response": "crisis_response",
            "summarize_history": "summarize_history"
        }
    )
    
    # Orden de la rama sin riesgo (CAM-03): summarize_history -> retrieve_quote -> counselor -> END
    workflow.add_edge("summarize_history", "retrieve_quote")
    workflow.add_edge("retrieve_quote", "counselor")
    workflow.add_edge("counselor", END)
    workflow.add_edge("crisis_response", END)
    
    # DEMO: Instanciación de MemorySaver: Estado en memoria del proceso: se pierde al reiniciar y no se comparte entre workers.
    checkpointer = MemorySaver()
    
    # Compilar el grafo con persistencia por thread_id
    app_graph = workflow.compile(checkpointer=checkpointer)
    return app_graph

app_graph = create_workflow()
