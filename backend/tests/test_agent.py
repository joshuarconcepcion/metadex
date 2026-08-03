from typing import List

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from backend.agents import advisor
from backend.agents.tools import meta_tools, pokemon_tools
from backend.rag import ingestion, store as rag_store_module
from backend.data import pvpoke


class FakeToolCallingChatModel(BaseChatModel):
    """Stands in for ChatAnthropic so no real Anthropic API call happens.

    Returns pre-scripted AIMessages in sequence — the first triggers a
    tool call, the second is the final answer after the tool result
    comes back. bind_tools() is a no-op passthrough: LangGraph's agent
    node only needs the bound model's .invoke() to keep returning
    messages, it doesn't require a fake model to actually attach
    provider-specific tool schemas.
    """

    responses: List[AIMessage] = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        response = self.responses.pop(0)
        return ChatResult(generations=[ChatGeneration(message=response)])

    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling"


def _tool_call_response(tool_name: str, args: dict, call_id: str = "call_1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": tool_name, "args": args, "id": call_id}])


def _final_response(text: str) -> AIMessage:
    return AIMessage(content=text)


@pytest.fixture
def small_rag_store(tmp_path_factory):
    """A minimal real Chroma store (real embeddings, no network) so
    search_meta has something to query against."""
    entries = [
        {
            "speciesId": "azumarill",
            "speciesName": "Azumarill",
            "moveset": ["BUBBLE", "ICE_BEAM", "HYDRO_PUMP"],
            "scores": [95.0, 70.0, 60.0, 55.0, 65.0, 97.0],
            "score": 88.2,
        },
    ]
    documents = pvpoke.rankings_to_documents({"great": entries}) + ingestion.ingest_mechanics()

    embeddings = rag_store_module.get_embeddings()
    persist_path = str(tmp_path_factory.mktemp("agent_chroma_store"))
    return rag_store_module.build_store(documents, embeddings, persist_path)


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(pvpoke.settings, "cache_path", str(tmp_path))


def _build_agent_with_fake_llm(monkeypatch, rag_store, responses: List[AIMessage]):
    fake_llm = FakeToolCallingChatModel(responses=list(responses))
    monkeypatch.setattr(advisor, "ChatAnthropic", lambda **kwargs: fake_llm)
    return advisor.build_advisor(rag_store)


def test_agent_calls_get_pokemon_info_for_pokemon_question(monkeypatch, small_rag_store):
    calls = []
    original_func = pokemon_tools.get_pokemon_info.func

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return original_func(*args, **kwargs)

    monkeypatch.setattr(pokemon_tools.get_pokemon_info, "func", spy)

    agent = _build_agent_with_fake_llm(
        monkeypatch,
        small_rag_store,
        [
            _tool_call_response("get_pokemon_info", {"pokemon_name": "medicham"}),
            _final_response("Medicham has base attack 121, defense 152, stamina 155."),
        ],
    )

    result = agent.invoke({"messages": [("user", "What are Medicham's stats?")]})

    assert len(calls) == 1
    call_args, call_kwargs = calls[0]
    pokemon_name_arg = call_kwargs.get("pokemon_name") or (call_args[0] if call_args else None)
    assert pokemon_name_arg == "medicham"
    final_message = result["messages"][-1]
    assert "121" in final_message.content


def test_agent_calls_search_meta_for_tier_list_question(monkeypatch, small_rag_store):
    calls = []
    original_func = meta_tools.search_meta.func

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return original_func(*args, **kwargs)

    monkeypatch.setattr(meta_tools.search_meta, "func", spy)

    agent = _build_agent_with_fake_llm(
        monkeypatch,
        small_rag_store,
        [
            _tool_call_response("search_meta", {"query": "best great league team", "league": "great"}),
            _final_response("Azumarill is a strong pick in Great League right now."),
        ],
    )

    result = agent.invoke({"messages": [("user", "What's a good Great League tier list team?")]})

    assert len(calls) == 1
    final_message = result["messages"][-1]
    assert "Azumarill" in final_message.content


def test_agent_calls_calculate_pvp_ivs_when_ivs_are_mentioned(monkeypatch, small_rag_store):
    calls = []
    original_func = pokemon_tools.calculate_pvp_ivs.func

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return original_func(*args, **kwargs)

    monkeypatch.setattr(pokemon_tools.calculate_pvp_ivs, "func", spy)

    iv_args = {
        "pokemon_name": "medicham",
        "iv_attack": 7,
        "iv_defense": 15,
        "iv_stamina": 14,
        "league": "great",
    }

    agent = _build_agent_with_fake_llm(
        monkeypatch,
        small_rag_store,
        [
            _tool_call_response("calculate_pvp_ivs", iv_args),
            _final_response("Those IVs hit exactly 1500 CP at level 49 — a great Great League spread."),
        ],
    )

    result = agent.invoke(
        {"messages": [("user", "Are 7/15/14 IVs good on my Medicham for Great League?")]}
    )

    assert len(calls) == 1
    call_args, call_kwargs = calls[0]
    iv_attack_arg = call_kwargs.get("iv_attack") if call_kwargs else call_args[1]
    assert iv_attack_arg == 7
    final_message = result["messages"][-1]
    assert "1500" in final_message.content
