# Standard Library
import abc
from dataclasses import dataclass, fields
from typing import Dict, List, Optional, Type, cast

# Third-party
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_active_plugins
from sematic.db.models.factories import make_user
from sematic.db.models.user import User
from sematic.db.queries import get_user, save_user


class AbstractAuth(abc.ABC):
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


def get_auth_plugins(
    default: List[Type[AbstractPlugin]],
) -> List[Type[AbstractAuth]]:
    """
    Return all configured "PUBLISH" scope plugins.
    """
    publisher_plugins = get_active_plugins(scope=PluginScope.PUBLISH, default=default)

    publisher_classes = [
        cast(Type[AbstractAuth], plugin) for plugin in publisher_plugins
    ]

    return publisher_classes


@dataclass(init=False)
class OIDCUser:
    """
    OpenID Connect Standard Claims
    https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
    """

    email: str
    given_name: str
    family_name: str
    picture: str

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


def get_user_from_oidc(oidc_user: OIDCUser) -> User:
    try:
        user = get_user(oidc_user.email)
        # In case these have changed
        user.first_name = oidc_user.given_name
        user.last_name = oidc_user.family_name
        user.avatar_url = oidc_user.picture
    except NoResultFound:
        user = make_user(
            email=oidc_user.email,
            first_name=oidc_user.given_name,
            last_name=oidc_user.family_name,
            avatar_url=oidc_user.picture,
        )

    user = save_user(user)
    return user


def is_email_domain_authorized(domain: Optional[str]) -> bool:
    authorized_email_domain = get_server_setting(
        ServerSettingsVar.SEMATIC_AUTHORIZED_EMAIL_DOMAIN, None
    )

    if authorized_email_domain is None:
        return True

    return domain in authorized_email_domain.split(",")
