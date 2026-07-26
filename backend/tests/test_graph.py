import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.workflow import create_workflow

@pytest.fixture
def mock_llm():
    with patch("app.graph.nodes.get_llm") as mock:
        llm_instance = MagicMock()
        llm_instance.invoke.return_value = AIMessage(content="Respuesta simulada del consejero para pruebas.")
        mock.return_value = llm_instance
        yield mock

def test_crisis_tiene_prioridad(mock_llm):
    """CAM-09: Mensaje con riesgo explícito -> pasa por crisis_response, NO por retrieve_quote ni counselor."""
    graph = create_workflow()
    config = {"configurable": {"thread_id": "test-crisis-1"}}
    input_state = {"messages": [HumanMessage(content="Quiero hacerme daño y terminar con todo")]}
    
    result = graph.invoke(input_state, config=config)
    
    assert result.get("is_crisis") is True
    # mock_llm no debió ser llamado para el nodo counselor
    mock_llm.return_value.invoke.assert_not_called()
    assert "recursos de emergencia" in result["messages"][-1].content or "doloroso" in result["messages"][-1].content

def test_ruta_normal(mock_llm):
    """CAM-09: Mensaje neutro -> pasa por retrieve_quote y counselor; no por crisis_response."""
    graph = create_workflow()
    config = {"configurable": {"thread_id": "test-normal-1"}}
    input_state = {"messages": [HumanMessage(content="Estoy sintiendo mucho estrés por el trabajo")]}
    
    result = graph.invoke(input_state, config=config)
    
    assert result.get("is_crisis") is False
    # mock_llm debió invocarse en el nodo counselor
    mock_llm.return_value.invoke.assert_called_once()
    assert result["messages"][-1].content == "Respuesta simulada del consejero para pruebas."

def test_sin_cita_disponible(mock_llm):
    """CAM-09: Tema sin cita en el banco -> el grafo completa; counselor recibió la cita como ausente (None)."""
    graph = create_workflow()
    config = {"configurable": {"thread_id": "test-no-quote-1"}}
    # Texto sin coincidencias de temas
    input_state = {"messages": [HumanMessage(content="xyz123 no_theme_match_qwerty")]}
    
    result = graph.invoke(input_state, config=config)
    
    assert result.get("selected_quote") is None
    assert result.get("is_crisis") is False
    mock_llm.return_value.invoke.assert_called()

def test_contexto_persiste(mock_llm):
    """CAM-09: Dos turnos con el mismo thread_id -> el segundo turno ve el historial del primero."""
    graph = create_workflow()
    config = {"configurable": {"thread_id": "test-persist-1"}}
    
    # Turno 1
    input_1 = {"messages": [HumanMessage(content="Hola, me llamo Carlos")]}
    graph.invoke(input_1, config=config)
    
    # Turno 2
    input_2 = {"messages": [HumanMessage(content="¿Cómo me llamo?")]}
    result_2 = graph.invoke(input_2, config=config)
    
    # El historial final debe tener 4 mensajes (Human1, AI1, Human2, AI2)
    messages = result_2.get("messages", [])
    assert len(messages) == 4
    assert messages[0].content == "Hola, me llamo Carlos"
    assert messages[2].content == "¿Cómo me llamo?"
