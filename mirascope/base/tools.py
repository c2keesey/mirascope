"""A base tool class for easy use of tools with prompts."""
from __future__ import annotations

from abc import ABC, abstractmethod
from inspect import Parameter, signature
from typing import Any, Callable, Type, TypeVar, cast, get_type_hints

from docstring_parser import parse
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


class BaseTool(BaseModel, ABC):
    """A base class for easy use of tools with prompts.

    `BaseTool` is an abstract class interface and should not be used directly.
    """

    @property
    def args(self) -> dict[str, Any]:
        """The arguments of the tool as a dictionary."""
        return self.model_dump(exclude={"tool_call"})

    @property
    def fn(self) -> Callable:
        """Returns the function that the tool describes."""
        raise RuntimeError("Tool does not have an attached function.")

    @classmethod
    def tool_schema(cls) -> Any:
        """Constructs a tool schema from the `BaseModel` schema defined."""
        model_schema = cls.model_json_schema()
        if "description" not in model_schema:
            raise ValueError("Tool must have a docstring description.")

        fn = {
            "name": model_schema["title"],
            "description": model_schema["description"],
        }
        if model_schema["properties"]:
            fn["parameters"] = {
                "type": "object",
                "properties": {
                    prop: {key: value for key, value in prop_schema.items()}
                    for prop, prop_schema in model_schema["properties"].items()
                    if prop != "tool_call"
                },
                "required": [
                    prop for prop in model_schema["required"] if prop != "tool_call"
                ]
                if "required" in model_schema
                else [],
                "$defs": {
                    key: value
                    for key, value in model_schema["$defs"].items()
                    if key != "ChatCompletionMessageToolCall" and key != "Function"
                }
                if "$defs" in model_schema
                else {},
            }
        return fn

    @classmethod
    @abstractmethod
    def from_tool_call(cls, tool_call: Any) -> BaseTool:
        """Extracts an instance of the tool constructed from a tool call response."""
        raise NotImplementedError()


T = TypeVar("T")
BaseToolT = TypeVar("BaseToolT", bound=BaseTool)


def tool_fn(fn: Callable) -> Callable[[Type[BaseToolT]], Type[BaseToolT]]:
    """A decorator for adding a function to a tool class.

    Adding this decorator will add an `fn` property to the tool class that returns the
    function that the tool describes. This is convenient for calling the function given
    an instance of the tool.

    Args:
        fn: The function to add to the tool class.

    Returns:
        The decorated tool class.
    """

    def decorator(cls: Type[BaseToolT]) -> Type[BaseToolT]:
        """A decorator for adding a function to a tool class."""
        setattr(cls, "fn", property(lambda self: fn))
        return cls

    return decorator


def convert_function_to_tool(fn: Callable, base: Type[BaseToolT]) -> Type[BaseToolT]:
    """Constructs a `BaseToolT` type from the given function.

    This method expects all function parameters to be properly documented in identical
    order with identical variable names, as well as descriptions of each parameter.
    Errors will be raised if any of these conditions are not met.

    Args:
        fn: The function to convert.

    Returns:
        The constructed `BaseToolT` type.

    Raises:
        ValueError: if the given function doesn't have a docstring.
        ValueError: if the given function's parameters don't have type annotations.
        ValueError: if a given function's parameter is in the docstring args section but
            the name doesn't match the docstring's parameter name.
        ValueError: if a given function's parameter is in the docstring args section but
            doesn't have a dosctring description.
    """
    if not fn.__doc__:
        raise ValueError("Function must have a docstring.")

    docstring = parse(fn.__doc__)

    doc = ""
    if docstring.short_description:
        doc = docstring.short_description
    if docstring.long_description:
        doc += "\n\n" + docstring.long_description

    field_definitions = {}
    hints = get_type_hints(fn)
    for i, parameter in enumerate(signature(fn).parameters.values()):
        if parameter.name == "self" or parameter.name == "cls":
            continue
        if parameter.annotation == Parameter.empty:
            raise ValueError("All parameters must have a type annotation.")

        docstring_description = None
        if i < len(docstring.params):
            docstring_param = docstring.params[i]
            if docstring_param.arg_name != parameter.name:
                raise ValueError(
                    f"Function parameter name {parameter.name} does not match docstring "
                    f"parameter name {docstring_param.arg_name}. Make sure that the "
                    "parameter names match exactly."
                )
            if not docstring_param.description:
                raise ValueError("All parameters must have a description.")
            docstring_description = docstring_param.description

        field_info = FieldInfo(annotation=hints[parameter.name])
        if parameter.default != Parameter.empty:
            field_info.default = parameter.default
        if docstring_description:  # we check falsy here because this comes from docstr
            field_info.description = docstring_description

        param_name = parameter.name
        if param_name.startswith("model_"):  # model_ is a BaseModel reserved namespace
            param_name = "aliased_" + param_name
            field_info.alias = parameter.name
            field_info.validation_alias = parameter.name
            field_info.serialization_alias = parameter.name

        field_definitions[param_name] = (
            hints[parameter.name],
            field_info,
        )

    return create_model(
        "".join(word.title() for word in fn.__name__.split("_")),
        __base__=tool_fn(fn)(base),
        __doc__=doc,
        **cast(dict[str, Any], field_definitions),
    )


def convert_base_model_to_tool(
    schema: Type[BaseModel], base: Type[BaseToolT]
) -> Type[BaseToolT]:
    """Converts a `BaseModel` schema to a `BaseToolT` type.

    By adding a docstring (if needed) and passing on fields and field information in
    dictionary format, a Pydantic `BaseModel` can be converted into an `BaseToolT` for
    performing extraction.

    Args:
        schema: The `BaseModel` schema to convert.

    Returns:
        The constructed `BaseToolT` type.
    """
    internal_doc = (
        f"An `{schema.__name__}` instance with correctly formatted and typed parameters "
        "extracted from the completion. Must include required parameters and may "
        "exclude optional parameters unless present in the text."
    )
    field_definitions = {
        field_name: (field_info.annotation, field_info)
        for field_name, field_info in schema.model_fields.items()
    }
    return create_model(
        f"{schema.__name__}Tool",
        __base__=base,
        __doc__=schema.__doc__ if schema.__doc__ else internal_doc,
        **cast(dict[str, Any], field_definitions),
    )


def convert_base_type_to_tool(
    schema: Type[T], base: Type[BaseToolT]
) -> Type[BaseToolT]:
    """Converts a `BaseType` to a `BaseToolT` type."""
    return create_model(
        f"{schema.__name__[0].upper()}{schema.__name__[1:]}Tool",
        __base__=base,
        __doc__=f"A tool for extracting a `{schema.__name__}` from the completion.",
        value=(schema, ...),
    )
