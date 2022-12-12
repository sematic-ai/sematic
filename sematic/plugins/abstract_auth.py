# Standard Library
import abc
from typing import Dict


class AbstractAuth(abc.ABC):
    pass

    @classmethod
    @abc.abstractmethod
    def get_public_auth_details(cls) -> Dict[str, str]:
        pass

    @classmethod
    @abc.abstractmethod
    def get_login_endpoint(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def get_slug(cls) -> str:
        pass
