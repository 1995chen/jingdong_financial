# -*- coding: utf-8 -*-


"""
application exception code map
"""

from infra.enums import StatusCode

__all__ = ["CODE_MAP"]

CODE_MAP = {
    StatusCode.UNEXPECTED_ERROR: "Internal server error",
    # app code
    StatusCode.APP_ERROR: "Application error",
    StatusCode.APP_CONFIG_LOAD_ERROR: "failed to load config",
    StatusCode.APP_INVALID_TYPE: "invalid type",
    StatusCode.APP_NOT_FOUND: "not found",
    StatusCode.APP_PYDANTIC_ERROR: "invalid param",
    StatusCode.APP_HANDLER_NOT_CALLABLE: "Handler not callable",
    StatusCode.APP_NOT_IMPLEMENTED: "Not implemented",
    StatusCode.APP_RPC_ERROR: "Rpc Server Error",
    StatusCode.APP_BLOOM_FILTER_ERROR: "Bloom filter denied",
    # web application code
    StatusCode.WEB_APP_ERROR: "Rest api error",
    StatusCode.WEB_APP_BAD_REQUEST: "Bad request",
    StatusCode.WEB_APP_AUTHENTICATION_FAILED: "Authentication failed",
    StatusCode.WEB_APP_PERMISSION_DENIED: "Permission denied",
    StatusCode.WEB_APP_INVALID_TOKEN: "Invalid token",
    StatusCode.WEB_APP_AUTHORIZED_FAIL: "Authorized failed",
    StatusCode.SUCCESS: "success",
}
