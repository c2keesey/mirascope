"""Tests the `cohere.stream` module."""

from cohere.types import (
    ApiMeta,
    ApiMetaBilledUnits,
    ChatMessage,
    NonStreamedChatResponse,
    StreamedChatResponse_StreamEnd,
    StreamedChatResponse_StreamStart,
    StreamedChatResponse_TextGeneration,
)

from mirascope.core.cohere.call_response import CohereCallResponse
from mirascope.core.cohere.call_response_chunk import CohereCallResponseChunk
from mirascope.core.cohere.stream import CohereStream


def test_cohere_stream() -> None:
    """Tests the `CohereStream` class."""
    assert CohereStream._provider == "cohere"
    chunks = [
        StreamedChatResponse_StreamStart(generation_id="id"),
        StreamedChatResponse_TextGeneration(
            text="content",
        ),
        StreamedChatResponse_StreamEnd(
            finish_reason="COMPLETE",
            response=NonStreamedChatResponse(
                generation_id="id",
                text="content",
                meta=ApiMeta(
                    billed_units=ApiMetaBilledUnits(input_tokens=1, output_tokens=1)
                ),
            ),
        ),
    ]

    def generator():
        for chunk in chunks:
            call_response_chunk = CohereCallResponseChunk(chunk=chunk)
            yield call_response_chunk, None

    stream = CohereStream(
        stream=generator(),
        metadata={},
        tool_types=None,
        call_response_type=CohereCallResponse,
        model="command-r-plus",
        prompt_template="",
        fn_args={},
        dynamic_config=None,
        messages=[ChatMessage(role="CHATBOT", message="content")],  # type: ignore
        call_params={},
        call_kwargs={},
    )
    assert stream.cost is None
    for _ in stream:
        pass
    assert stream.cost == 1.8e-5
    assert stream.message_param == ChatMessage(
        role="assistant",  # type: ignore
        message="content",
        tool_calls=None,
    )


def test_construct_call_response():
    chunks = [
        StreamedChatResponse_StreamStart(generation_id="id"),
        StreamedChatResponse_TextGeneration(
            text="content",
        ),
        StreamedChatResponse_StreamEnd(
            finish_reason="COMPLETE",
            response=NonStreamedChatResponse(
                generation_id="id",
                text="content",
                meta=ApiMeta(
                    billed_units=ApiMetaBilledUnits(input_tokens=1, output_tokens=1)
                ),
            ),
        ),
    ]

    def generator():
        for chunk in chunks:
            call_response_chunk = CohereCallResponseChunk(chunk=chunk)
            yield call_response_chunk, None

    stream = CohereStream(
        stream=generator(),
        metadata={},
        tool_types=None,
        call_response_type=CohereCallResponse,
        model="command-r-plus",
        prompt_template="",
        fn_args={},
        dynamic_config=None,
        messages=[ChatMessage(role="CHATBOT", message="content")],  # type: ignore
        call_params={},
        call_kwargs={},
    )
    assert stream.cost is None
    for _ in stream:
        pass
    constructed_call_response = stream.construct_call_response()
    usage = ApiMetaBilledUnits(input_tokens=1, output_tokens=1)
    completion = NonStreamedChatResponse(
        generation_id="id",
        text="content",
        finish_reason="COMPLETE",
        meta=ApiMeta(billed_units=usage),
    )
    call_response = CohereCallResponse(
        metadata={},
        response=completion,
        tool_types=None,
        prompt_template="",
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        user_message_param=None,
        start_time=0,
        end_time=0,
    )
    assert constructed_call_response._provider == call_response._provider
    assert constructed_call_response.content == call_response.content
    assert constructed_call_response.finish_reasons == call_response.finish_reasons
    assert constructed_call_response.model == call_response.model
    assert constructed_call_response.id == call_response.id
    assert constructed_call_response.usage == call_response.usage
    assert constructed_call_response.input_tokens == call_response.input_tokens
    assert constructed_call_response.output_tokens == call_response.output_tokens
    assert constructed_call_response.cost == call_response.cost
    assert constructed_call_response.message_param == call_response.message_param
