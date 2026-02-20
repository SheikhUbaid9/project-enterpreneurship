from app.adapters.base_adapter import BaseGatewayPlatformAdapter
from app.adapters.email_gateway_adapter import EmailGatewayAdapter
from app.adapters.slack_gateway_adapter import SlackGatewayAdapter
from app.adapters.whatsapp_gateway_adapter import WhatsAppGatewayAdapter


class AdapterFactory:
    def __init__(self):
        self._adapters: dict[str, BaseGatewayPlatformAdapter] = {
            "email": EmailGatewayAdapter(),
            "slack": SlackGatewayAdapter(),
            "whatsapp": WhatsAppGatewayAdapter(),
        }

    def get(self, platform: str) -> BaseGatewayPlatformAdapter:
        if platform not in self._adapters:
            raise ValueError(f"Unsupported platform '{platform}'")
        return self._adapters[platform]

    def all(self) -> list[BaseGatewayPlatformAdapter]:
        return list(self._adapters.values())
