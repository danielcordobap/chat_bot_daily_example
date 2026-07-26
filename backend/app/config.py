import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = ""
    # CAM-01: MODEL_ID verificado con precio 0 en OpenRouter
    MODEL_ID: str = "inclusionai/ling-3.0-flash:free"
    
    # CAM-01: Lista de fallbacks verificados exclusivamente presentes en la llamada real a OpenRouter con precio 0
    VERIFIED_FREE_FALLBACKS: list[str] = [
        "inclusionai/ling-3.0-flash:free",
        "poolside/laguna-s-2.1:free",
        "poolside/laguna-xs-2.1:free",
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "google/gemma-4-31b-it:free",
        "openai/gpt-oss-20b:free"
    ]
    
    # CAM-03: Umbral nombrado para compresión de historial
    MAX_HISTORY_MESSAGES: int = 10
    
    # Configuración de Servidor y CORS
    # pydantic-settings parsea los tipos complejos (list[str]) con json.loads: un valor de .env
    # separado por comas aborta el arranque. Se declara str y se separa en Python.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def allowed_origins_list(self) -> list[str]:
        """Orígenes CORS a partir de la cadena separada por comas."""
        raw = self.ALLOWED_ORIGINS.strip()
        # Un valor en formato JSON produce orígenes inválidos y CORS falla en silencio: el
        # navegador bloquea la respuesta y el backend no registra nada. Se aborta el arranque.
        if raw.startswith("[") or '"' in raw or "'" in raw:
            raise ValueError(
                "ALLOWED_ORIGINS debe ir separado por comas, sin corchetes ni comillas.\n"
                "  Correcto: ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173\n"
                f"  Recibido: ALLOWED_ORIGINS={raw}"
            )
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        # Degradación: una cadena vacía dejaría CORS sin orígenes y el frontend no podría
        # llamar al backend. Se cae al valor por defecto en lugar de bloquear todo.
        return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
