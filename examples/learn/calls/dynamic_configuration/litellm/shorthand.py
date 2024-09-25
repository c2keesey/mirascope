from mirascope.core import BaseDynamicConfig, Messages, litellm


@litellm.call("gpt-4o-mini")
def recommend_book(genre: str) -> BaseDynamicConfig:
    return {
        "messages": [Messages.User(f"Recommend a {genre} book")],
        "call_params": {"max_tokens": 512},
        "metadata": {"tags": {"version:0001"}},
    }


print(recommend_book("fantasy"))
