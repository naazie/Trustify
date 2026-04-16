from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongo_uri: str = "mongodb://localhost:27017/trustify"
    gemini_api_key: str = ""
    workspace_dir: str = "/tmp/trustify_workspaces"
    host_workspace_dir: str = "/tmp/trustify_workspaces"
    environment: str = "development"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    frontend_url: str = "http://localhost:3000"

    # Tool Docker image tags
    semgrep_image: str = "returntocorp/semgrep:latest"
    gitleaks_image: str = "zricethezav/gitleaks:latest"
    pylint_image: str = "cytopia/pylint:latest"
    eslint_image: str = "node:20-alpine"


settings = Settings()
