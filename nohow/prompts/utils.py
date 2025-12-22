from typing import Type
from langchain.messages import HumanMessage, AIMessage, AnyMessage


def new_message_of_type(
    type: Type[HumanMessage | AIMessage], content: str = ""
) -> HumanMessage | AIMessage:
    """Create a new message of the given type with default content."""
    if type == HumanMessage:
        return HumanMessage(content=content)
    elif type == AIMessage:
        return AIMessage(content=content)
    else:
        raise ValueError(f"Unsupported message type: {type}")
