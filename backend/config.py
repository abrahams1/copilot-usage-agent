from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Entra ID / Graph
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_subscription_ids: str = ""

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-10-21"

    # Behavior
    use_mock_data: bool = True
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    # MCP commands
    workiq_mcp_cmd: str = "python -m backend.mcp_servers.workiq_server"
    foundryiq_mcp_cmd: str = "python -m backend.mcp_servers.foundryiq_server"
    copilot_studio_mcp_cmd: str = "python -m backend.mcp_servers.copilot_studio_server"

    @property
    def subscription_list(self) -> list[str]:
        if not self.azure_subscription_ids:
            return []
        return [s.strip() for s in self.azure_subscription_ids.split(",") if s.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
