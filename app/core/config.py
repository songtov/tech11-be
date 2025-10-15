from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "supersecret"
    PROJECT_NAME: str = "FastAPI Tech11 Backend"

    # Azure OpenAI Configuration
    AOAI_ENDPOINT: str = ""
    AOAI_API_KEY: str = ""
    AOAI_DEPLOY_GPT4O_MINI: str = "gpt-4o-mini"
    AOAI_DEPLOY_GPT4O: str = "gpt-4o"
    AOAI_DEPLOY_EMBED_3_LARGE: str = "text-embedding-3-large"
    AOAI_DEPLOY_EMBED_3_SMALL: str = "text-embedding-3-small"
    AOAI_DEPLOY_EMBED_ADA: str = "text-embedding-ada-002"

    # TTS config
    TTS_ENDPOINT: str = "https://api.typecast.ai/v1/text-to-speech"
    TTS_API_KEY: str = ""
    TTS_VOICE_ID: str = ""
    TTS_MODEL: str = "ssfm-v21"
    TTS_LANGUAGE: str = "kor"
    TTS_EMOTION_PRESET: str = "normal"
    TTS_EMOTION_INTENSITY: int = 1
    TTS_VOLUME: int = 100
    TTS_AUDIO_PITCH: int = 0
    TTS_AUDIO_TEMPO: int = 1

    # S3 Bucket
    S3_BUCKET: str = ""
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
