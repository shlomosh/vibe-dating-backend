from abc import abstractmethod
from typing import Any, Callable, Dict, Optional


class CommonPlatform:
    def __init__(
        self,
        platform: str,
        platform_token: str,
        get_secret_f: Optional[Callable[[str], str]] = None,
    ):
        self.platform = platform
        self.platform_token = platform_token

        if get_secret_f is None:
            from core.aws import SecretsManagerService

            self.get_secret_f = SecretsManagerService.get_secret
        else:
            self.get_secret_f = get_secret_f

    @abstractmethod
    def authenticate(self, platform_token: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError()
