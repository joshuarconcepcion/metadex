"""Wraps the advisor agent with persistent message history.

Two things here needed hands-on verification before writing this file,
not just reading the docs:

1. RunnableWithMessageHistory cannot wrap create_agent()'s compiled graph
   directly. The graph's output is the ENTIRE accumulated conversation
   (input messages + everything the graph added), but
   RunnableWithMessageHistory independently appends both "the input
   messages" and "the output messages" to history — so if the output
   already contains a copy of the input, every turn re-saves the whole
   prior history on top of itself. Verified experimentally: after two
   turns, message count was compounding (9 stored messages for what
   should have been 4). The fix is _strip_to_new_messages() below, which
   wraps the agent so its output only contains what it added this turn.

2. RunnableWithMessageHistory's own .stream(), given a RunnableLambda
   wrapping a LangGraph agent, does not yield real token-by-token
   output — a plain Python-function-based Runnable has no notion of
   incremental generation, so .stream() just invokes once and yields the
   single final result. Genuine token streaming needs the compiled
   agent's own .stream(..., stream_mode="messages"), which yields
   (message_chunk, metadata) pairs as the model actually generates them —
   verified against a fake streaming chat model with zero API cost.
   stream_query() below uses that directly rather than going through
   RunnableWithMessageHistory for the streaming path.
"""
import uuid
from typing import Generator

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory

from backend.agents.advisor import build_advisor
from backend.agents.memory import get_session_history


def _strip_to_new_messages(agent) -> RunnableLambda:
    """Wraps a compiled LangGraph agent so invoke() returns only the
    messages it added this turn, not the full accumulated conversation —
    see the module docstring for why this matters."""

    def invoke(input_dict: dict, config: dict = None) -> dict:
        input_length = len(input_dict["messages"])
        result = agent.invoke(input_dict, config=config)
        return {"messages": result["messages"][input_length:]}

    return RunnableLambda(invoke)


def build_chain(rag_store: Chroma) -> RunnableWithMessageHistory:
    """Wraps the advisor agent with persistent SQLChatMessageHistory so
    conversations survive server restarts."""
    agent = build_advisor(rag_store)
    new_messages_only = _strip_to_new_messages(agent)

    return RunnableWithMessageHistory(
        new_messages_only,
        get_session_history,
        input_messages_key="messages",
        history_messages_key=None,
        output_messages_key="messages",
    )


def query(question: str, session_id: str, rag_store: Chroma) -> str:
    """Runs the chain for one question and returns the final text response."""
    session_id = session_id or str(uuid.uuid4())
    chain = build_chain(rag_store)

    result = chain.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"session_id": session_id}},
    )

    final_message = result["messages"][-1]
    return final_message.content


def stream_query(question: str, session_id: str, rag_store: Chroma) -> Generator[str, None, None]:
    """Streams the agent's response token by token, then persists the turn.

    Loads history directly and calls the compiled agent's native
    stream_mode="messages" rather than routing through
    RunnableWithMessageHistory (see module docstring) — history is saved
    manually once the full response text is known.
    """
    session_id = session_id or str(uuid.uuid4())
    agent = build_advisor(rag_store)
    history = get_session_history(session_id)

    input_messages = list(history.messages) + [HumanMessage(content=question)]

    response_chunks = []
    for message_chunk, metadata in agent.stream({"messages": input_messages}, stream_mode="messages"):
        # Tool-call and tool-result chunks pass through here too; only the
        # model node's actual text generation has non-empty content.
        if metadata.get("langgraph_node") == "model" and message_chunk.content:
            response_chunks.append(message_chunk.content)
            yield message_chunk.content

    history.add_user_message(question)
    history.add_ai_message("".join(response_chunks))
