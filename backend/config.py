from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongo_uri: str = "mongodb://localhost:27017/trustify"
    gemini_api_key: str = ""
    workspace_dir: str = "/tmp/trustify_workspaces"
    environment: str = "development"

    # Tool Docker image tags
    semgrep_image: str = "returntocorp/semgrep:latest"
    gitleaks_image: str = "zricethezav/gitleaks:latest"
    pylint_image: str = "cytopia/pylint:latest"


settings = Settings()
