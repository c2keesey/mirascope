"""Mirascope x Langfuse Integration."""

from langfuse.decorators import observe

from ..middleware_factory import middleware_decorator
from ._utils import (
    handle_call_response,
    handle_call_response_async,
    handle_response_model,
    handle_response_model_async,
    handle_stream,
    handle_stream_async,
    handle_structured_stream,
    handle_structured_stream_async,
)


def with_langfuse(fn):
    """Wraps a Mirascope function with Langfuse."""

    return middleware_decorator(
        fn,
        custom_decorator=observe(
            name=fn.__name__,
            as_type="generation",
            capture_input=False,
            capture_output=False,
        ),
        handle_call_response=handle_call_response,
        handle_call_response_async=handle_call_response_async,
        handle_stream=handle_stream,
        handle_stream_async=handle_stream_async,
        handle_response_model=handle_response_model,
        handle_response_model_async=handle_response_model_async,
        handle_structured_stream=handle_structured_stream,
        handle_structured_stream_async=handle_structured_stream_async,
    )
