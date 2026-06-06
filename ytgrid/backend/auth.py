import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from ytgrid.utils.config import config

API_KEY_NAME = "X-API-Key"

# The key may arrive as a header (CLI / API clients) or as a query parameter
# (browser EventSource connections, which cannot set custom headers).
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def verify_api_key(
    header_key: str = Security(api_key_header),
    query_key: str = Security(api_key_query),
):
    """Validate the request API key.

    When ``YTGRID_API_KEY`` is unset, authentication is disabled and every
    request is allowed (returns ``None``). When set, a matching key must be
    supplied via the ``X-API-Key`` header or the ``api_key`` query parameter.
    """
    if not config.API_KEY:
        return None

    provided = header_key or query_key
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
        )
    if not secrets.compare_digest(provided, config.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate API key",
        )
    return provided
