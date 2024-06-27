"""The `gemini_call_async` decorator for easy Gemini API typed functions."""

from ..base import call_async_factory
from ._create_async import create_async_decorator
from ._extract_async import extract_async_decorator
from ._stream_async import GeminiAsyncStream, stream_async_decorator
from ._structured_stream_async import structured_stream_async_decorator
from .call_params import GeminiCallParams
from .call_response import GeminiCallResponse
from .call_response_chunk import GeminiCallResponseChunk
from .function_return import GeminiDynamicConfig

gemini_call_async = call_async_factory(
    GeminiCallResponse,
    GeminiCallResponseChunk,
    GeminiCallParams,
    GeminiDynamicConfig,
    GeminiAsyncStream,
    create_async_decorator,
    stream_async_decorator,
    extract_async_decorator,
    structured_stream_async_decorator,
)
'''A decorator for calling the Gemini API with a typed function.

This decorator is used to wrap a typed function that calls the Gemini API. It parses
the docstring of the wrapped function as the messages array and templates the input
arguments for the function into each message's template.

Example:

```python
@gemini_call(model="gemini-1.5-pro")
def recommend_book(genre: str):
    """Recommend a {genre} book."""

response = recommend_book("fantasy")
```

Args:
    model: The Gemini model to use in the API call.
    stream: Whether to stream the response from the API call.
    tools: The tools to use in the Gemini API call.
    **call_params: The `GeminiCallParams` call parameters to use in the API call.

Returns:
    The decorator for turning a typed function into an Gemini API call.
'''
