"""
Custom Response Classes for Performance Optimization
Uses orjson for 2-3x faster JSON serialization
"""
from typing import Any
import orjson
from fastapi.responses import JSONResponse


class ORJSONResponse(JSONResponse):
    """
    Custom JSON response using orjson for faster serialization.

    orjson is 2-3x faster than standard json library and handles
    datetime, UUID, and other types automatically.

    Usage:
        @app.get("/endpoint", response_class=ORJSONResponse)
        async def endpoint():
            return {"key": "value"}

    Or set as default:
        app = FastAPI(default_response_class=ORJSONResponse)
    """

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        """
        Render content to JSON bytes using orjson.

        orjson options:
        - OPT_INDENT_2: Not used for production (smaller response)
        - OPT_SERIALIZE_NUMPY: Handle numpy arrays if needed
        - OPT_NON_STR_KEYS: Allow non-string dict keys
        - OPT_SORT_KEYS: Sort keys for consistent output
        """
        return orjson.dumps(
            content,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )


class PrettyORJSONResponse(ORJSONResponse):
    """
    Pretty-printed JSON response using orjson (for debugging).

    Usage:
        @app.get("/debug", response_class=PrettyORJSONResponse)
        async def debug_endpoint():
            return {"key": "value"}
    """

    def render(self, content: Any) -> bytes:
        """Render content with indentation for debugging"""
        return orjson.dumps(
            content,
            option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )