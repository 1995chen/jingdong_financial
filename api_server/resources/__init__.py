# -*- coding: utf-8 -*-

"""
Here are some methods that are common to all apis.
The package should only be referenced by other modules in resources
"""

import gzip
import logging
from enum import Enum
from typing import Any, Callable, List, Optional, Type, Union
from urllib.parse import urljoin

import fastapi
import inject
import orjson
from fastapi import Request, Response
from fastapi.responses import JSONResponse, ORJSONResponse, RedirectResponse
from fastapi.routing import APIRoute
from starlette.types import ASGIApp

from infra.decorator.trace import EventIdTrace
from infra.dependencies import Auth, Config, Registry
from infra.utils import make_json_response, name_convert_to_snake

__all__ = [
    "APIDefaultRouter",
    "APIV1Router",
    "APIV2Router",
    "TemplateAPIRouter",
    "TemplateNoFormatAPIRouter",
    "bind_router",
]

config: Config = inject.instance(Config)
registry: Registry = inject.instance(Registry)
auth: Auth = inject.instance(Auth)
logger = logging.getLogger(__name__)


class GzipRequest(Request):  # type: ignore[misc]
    """
    fix gzip issue:
    https://stackoverflow.com/questions/65078775/accept-gzipped-body-in-fastapi-uvicorn
    """

    async def body(self) -> Any:
        """
        Here supports gzip and JSON
        """
        if not hasattr(self, "_body"):
            _body: bytes = await super().body()
            _body = gzip.decompress(_body)
            setattr(self, "_body", orjson.loads(_body))
        return self._body


class CustomOriginRoute(APIRoute):  # type: ignore[misc]
    """
    Custom API Route
    Does not process the original data
    """

    def get_route_handler(self) -> Any:
        original_route_handler = super().get_route_handler()

        @EventIdTrace.trace()
        async def custom_route_handler(request: Request) -> Response:
            try:
                logger.info(f"get request, content is {auth.get_request()}")
                # Extract specified parameters from request.url and store them in the Registry
            except (
                ValueError,
                IndexError,
            ):
                logger.warning(f"failed, url is {str(request.url)}", exc_info=True)
            if "gzip" in request.headers.getlist("Content-Encoding"):
                request = GzipRequest(request.scope, request.receive)
            response: Response = await original_route_handler(request)
            return response

        return custom_route_handler


class CustomJsonRoute(CustomOriginRoute):
    """
    Custom API Route
    Will process the returned JSON response
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            response: Response = await original_route_handler(request)
            # Here, you can customize the returned Response
            if isinstance(response, JSONResponse):
                # Do not process the format defined in app.utils.response pylint: disable=E1101
                content: Any = orjson.loads(response.body)
                if "code" not in content:
                    response = ORJSONResponse(
                        status_code=response.status_code,
                        content=make_json_response(data=content),
                    )
            return response

        return custom_route_handler


class APIDefaultRouter(fastapi.APIRouter):  # type: ignore[misc]
    """
    default api group
    """

    # pylint: disable=R0914
    def __init__(
        self,
        *,
        name: str = "",
        api_prefix: str = "",
        api_version: Optional[str] = None,
        sub_path: Optional[str] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        route_class: Type[APIRoute] = CustomJsonRoute,
    ) -> None:
        prefix: str = api_prefix
        if api_version:
            prefix = urljoin(f"{prefix}/", f"{api_version}/")
        if sub_path:
            prefix = urljoin(f"{prefix}/", f"{sub_path.lstrip('/')}/")
        if name:
            prefix = urljoin(f"{prefix}/", f"{name_convert_to_snake(name)}")
        # The prefix cannot end with /
        prefix = prefix.rstrip("/")
        super().__init__(
            # All APIs bound to this Router are defined as version v1 here
            prefix=prefix,
            tags=tags,
            redirect_slashes=redirect_slashes,
            default=default,
            route_class=route_class,
        )


class APIV1Router(APIDefaultRouter):
    """
    api group with v1
    """

    # pylint: disable=R0914
    def __init__(
        self,
        *,
        name: str = "",
        sub_path: Optional[str] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        route_class: Type[APIRoute] = CustomJsonRoute,
    ) -> None:
        super().__init__(
            name=name_convert_to_snake(name),
            api_prefix=config.API_PREFIX,
            api_version="v1",
            sub_path=sub_path,
            tags=tags,
            redirect_slashes=redirect_slashes,
            default=default,
            route_class=route_class,
        )


class APIV2Router(APIDefaultRouter):
    """
    api group with v2
    """

    # pylint: disable=R0914
    def __init__(
        self,
        *,
        name: str = "",
        sub_path: Optional[str] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        route_class: Type[APIRoute] = CustomJsonRoute,
    ) -> None:
        super().__init__(
            name=name_convert_to_snake(name),
            api_prefix=config.API_PREFIX,
            api_version="v2",
            sub_path=sub_path,
            tags=tags,
            redirect_slashes=redirect_slashes,
            default=default,
            route_class=route_class,
        )


class TemplateAPIRouter(APIV1Router):
    """
    template api group
    """

    # pylint: disable=R0914
    def __init__(
        self,
        *,
        name: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
    ) -> None:
        route_tags: List[Union[str, Enum]] = ["template"]
        if tags:
            route_tags.extend(tags)
        super().__init__(
            name=name,
            # You can customize the sub_path
            sub_path=None,
            tags=list(set(route_tags)),
            redirect_slashes=redirect_slashes,
            default=default,
        )


class TemplateNoFormatAPIRouter(APIV1Router):
    """
    template api group for without format response
    """

    # pylint: disable=R0914
    def __init__(
        self,
        *,
        name: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
    ) -> None:
        route_tags: List[Union[str, Enum]] = ["template"]
        if tags:
            route_tags.extend(tags)
        super().__init__(
            name=name,
            # You can customize the sub_path
            sub_path=None,
            tags=list(set(route_tags)),
            redirect_slashes=redirect_slashes,
            default=default,
            # Use the native route_class.
            # The default route_class of APIDefaultRouter will
            # unify the JSON format, which is not needed here
            route_class=CustomOriginRoute,
        )


def bind_router(application: fastapi.FastAPI) -> None:
    """
    Bind the routing table
    :param application: FastAPI instance
    """
    # prevent circle import
    # pylint: disable=C0415,R0401
    from . import demo, gold

    # Route list [can also be modified for automatic registration]
    routes: List[APIDefaultRouter] = []
    routes.extend(demo.get_routers())
    routes.extend(gold.get_routers())

    @application.get("/")
    async def index() -> RedirectResponse:
        return RedirectResponse(url="/static/index.html")

    for route in routes:
        application.include_router(route)
