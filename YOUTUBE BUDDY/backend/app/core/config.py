import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env", override=False)


class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "kumar project Backend")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    API_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "http://localhost:8000")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./dev.db",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TASK_ALWAYS_EAGER: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true"

    # OpenAI Configuration
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    OPENAI_IMAGE_MODEL: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    OPENAI_TRANSCRIPTION_MODEL: str = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
    AI_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "120"))

    # Hugging Face Configuration
    HUGGINGFACE_API_KEY: str | None = os.getenv("HUGGINGFACE_API_KEY")
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "microsoft/DialoGPT-medium")
    HUGGINGFACE_TEXT_MODEL: str = os.getenv("HUGGINGFACE_TEXT_MODEL", "microsoft/DialoGPT-medium")
    HUGGINGFACE_IMAGE_MODEL: str = os.getenv("HUGGINGFACE_IMAGE_MODEL", "stabilityai/stable-diffusion-2-1")
    HUGGINGFACE_AUDIO_MODEL: str | None = os.getenv("HUGGINGFACE_AUDIO_MODEL")

    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Google Gemini Configuration (Free tier: 15 RPM, 1M tokens/day)
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    # Groq API Configuration (Free tier ultra-fast LLaMA & Whisper)
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_WHISPER_MODEL: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

    # OpenRouter Configuration (Free tier compatible models)
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")

    ALLOW_REMOTE_INFERENCE: bool = os.getenv("ALLOW_REMOTE_INFERENCE", "False").lower() == "true"
    LOCAL_IMAGE_MODEL_PATH: str | None = os.getenv("LOCAL_IMAGE_MODEL_PATH")
    LOCAL_WHISPER_MODEL_PATH: str | None = os.getenv("LOCAL_WHISPER_MODEL_PATH")

    # Default AI Provider ("auto", "gemini", "groq", "openrouter", "ollama")
    AI_PROVIDER_DEFAULT: str = os.getenv("AI_PROVIDER_DEFAULT", "auto")

    # Security & CORS
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET", "super_secret_key_change_in_production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DEMO_LOGIN_EMAIL: str = os.getenv("DEMO_LOGIN_EMAIL", "demo@youtubebuddy.com")
    DEMO_LOGIN_PASSWORD: str = os.getenv("DEMO_LOGIN_PASSWORD", "Demo@12345")
    # Demo/dev login is only ever on in development/test unless explicitly forced on.
    ENABLE_DEMO_LOGIN: bool = os.getenv("ENABLE_DEMO_LOGIN", "False").lower() == "true"
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
    )

    def get_allowed_origins(self) -> list[str]:
        """Return parsed list of CORS allowed origins."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def demo_login_enabled(self) -> bool:
        return self.ENABLE_DEMO_LOGIN and self.ENVIRONMENT.lower() in {"development", "test"}

    def validate_production_security(self) -> None:
        """Enforce strict security parameters when running in production."""
        if self.ENVIRONMENT.lower() == "production":
            if "change_in_production" in self.JWT_SECRET_KEY or self.JWT_SECRET_KEY.startswith("local_demo_only") or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "FATAL SECURITY RISK: Production deployment requires a secure JWT_SECRET of at least 32 characters."
                )
            if "*" in self.get_allowed_origins():
                raise ValueError("FATAL SECURITY RISK: ALLOWED_ORIGINS must not contain '*' in production.")
            if self.ENABLE_DEMO_LOGIN:
                raise ValueError("FATAL SECURITY RISK: ENABLE_DEMO_LOGIN must be off in production.")

    # Storage
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    RENDER_DIR: str = os.getenv("RENDER_DIR", "rendered")
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "10737418240"))

    # Firebase Configuration - USED ONLY FOR:
    # - Google Login Authentication
    # - YouTube OAuth
    # - Firebase Storage (when STORAGE_PROVIDER=firebase)
    FIREBASE_PROJECT_ID: str | None = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_CLIENT_ID: str | None = os.getenv("FIREBASE_CLIENT_ID")
    FIREBASE_CLIENT_EMAIL: str | None = os.getenv("FIREBASE_CLIENT_EMAIL")
    FIREBASE_PRIVATE_KEY: str | None = os.getenv("FIREBASE_PRIVATE_KEY")
    FIREBASE_STORAGE_BUCKET: str | None = os.getenv("FIREBASE_STORAGE_BUCKET")
    FIREBASE_SERVICE_ACCOUNT_PATH: str | None = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    FIREBASE_STORAGE_BASE_URL: str = "https://firebasestorage.googleapis.com/v0/b"

    # CDN / production file serving
    STORAGE_CDN_URL: str | None = os.getenv("STORAGE_CDN_URL")

    model_config = {"env_file": str(BACKEND_DIR / ".env")}


settings = Settings()
