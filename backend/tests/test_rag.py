import pytest

from backend.data import pvpoke
from backend.rag import ingestion, retriever, store


# --- Realistic-shaped PvPoke mock payloads ----------------------------------
# Field shapes here match the real, verified PvPoke rankings JSON: "moveset"
# is a flat [fastMove, chargedMove1, chargedMove2] array, and "scores" is an
# unlabeled 6-element array in [lead, closer, switch, charger, attacker,
# consistency] order (verified against PvPoke's own RankerOverall.js).

def _make_entry(species_id, species_name, moveset, scores, score, rating=650):
    return {
        "speciesId": species_id,
        "speciesName": species_name,
        "rating": rating,
        "matchups": [],
        "counters": [],
        "moves": {"fastMoves": [], "chargedMoves": []},
        "moveset": moveset,
        "score": score,
        "scores": scores,
        "editorScore": int(score),
        "editorNotes": "",
    }


GREAT_LEAGUE_SAMPLE = [
    _make_entry(
        "medicham", "Medicham", ["COUNTER", "POWER_UP_PUNCH", "ICE_PUNCH"],
        [88.0, 92.0, 85.0, 80.0, 95.0, 91.0], 90.5,
    ),
    _make_entry(
        "azumarill", "Azumarill", ["BUBBLE", "ICE_BEAM", "HYDRO_PUMP"],
        [95.0, 70.0, 60.0, 55.0, 65.0, 97.0], 88.2,
    ),
]

ULTRA_LEAGUE_SAMPLE = [
    _make_entry(
        "cresselia", "Cresselia", ["PSYCHO_CUT", "MOONBLAST", "GRASS_KNOT"],
        [80.0, 85.0, 90.0, 40.0, 88.0, 93.0], 86.0,
    ),
]

MASTER_LEAGUE_SAMPLE = [
    _make_entry(
        "dialga", "Dialga", ["DRAGON_BREATH", "IRON_HEAD", "DRACO_METEOR"],
        [70.0, 90.0, 92.0, 96.0, 80.0, 89.0], 92.1,
    ),
]


class _FakeResponse:
    """Stands in for httpx.Response so no real network call happens."""

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Never touch the developer's real cache directory from tests."""
    monkeypatch.setattr(pvpoke.settings, "cache_path", str(tmp_path))


# --- data/pvpoke.py ----------------------------------------------------------

def test_fetch_rankings_uses_mocked_http_not_real_network(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return _FakeResponse(GREAT_LEAGUE_SAMPLE)

    monkeypatch.setattr(pvpoke.httpx, "get", fake_get)

    result = pvpoke.fetch_rankings("great")

    assert result == GREAT_LEAGUE_SAMPLE
    assert calls == [pvpoke.PVPOKE_URLS["great"]]


def test_fetch_rankings_caches_and_skips_second_http_call(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return _FakeResponse(GREAT_LEAGUE_SAMPLE)

    monkeypatch.setattr(pvpoke.httpx, "get", fake_get)

    pvpoke.fetch_rankings("great")
    pvpoke.fetch_rankings("great")  # should hit the cache, not fetch again

    assert len(calls) == 1


def test_fetch_all_rankings_covers_all_three_leagues(monkeypatch):
    payloads = {
        pvpoke.PVPOKE_URLS["great"]: GREAT_LEAGUE_SAMPLE,
        pvpoke.PVPOKE_URLS["ultra"]: ULTRA_LEAGUE_SAMPLE,
        pvpoke.PVPOKE_URLS["master"]: MASTER_LEAGUE_SAMPLE,
    }

    def fake_get(url, timeout):
        return _FakeResponse(payloads[url])

    monkeypatch.setattr(pvpoke.httpx, "get", fake_get)

    result = pvpoke.fetch_all_rankings()

    assert set(result.keys()) == {"great", "ultra", "master"}
    assert result["great"] == GREAT_LEAGUE_SAMPLE
    assert result["ultra"] == ULTRA_LEAGUE_SAMPLE
    assert result["master"] == MASTER_LEAGUE_SAMPLE


def test_rankings_to_documents_structure():
    documents = pvpoke.rankings_to_documents({"great": GREAT_LEAGUE_SAMPLE})

    assert len(documents) == 2

    medicham_doc = documents[0]
    assert "Medicham is a top 1 Pokemon in Great League" in medicham_doc.page_content
    assert "rating of 90.5" in medicham_doc.page_content
    assert "COUNTER / POWER_UP_PUNCH, ICE_PUNCH" in medicham_doc.page_content
    assert "Lead: 88.0" in medicham_doc.page_content
    assert "Switch: 85.0" in medicham_doc.page_content
    assert "Closer: 92.0" in medicham_doc.page_content
    assert "Attacker: 95.0" in medicham_doc.page_content
    assert "Consistency: 91.0" in medicham_doc.page_content

    assert medicham_doc.metadata == {
        "source": "pvpoke",
        "league": "great",
        "species_id": "medicham",
        "species_name": "Medicham",
        "rank": 1,
        "rating": 90.5,
        "fast_move": "COUNTER",
        "charged_moves": ["POWER_UP_PUNCH", "ICE_PUNCH"],
    }


def test_rankings_to_documents_truncates_to_top_50_per_league():
    many_entries = [
        _make_entry(f"mon_{i}", f"Mon {i}", ["FAST", "CHARGE_A", "CHARGE_B"], [50.0] * 6, 100 - i)
        for i in range(60)
    ]

    documents = pvpoke.rankings_to_documents({"great": many_entries})

    assert len(documents) == 50
    assert documents[0].metadata["rank"] == 1
    assert documents[-1].metadata["rank"] == 50


# --- rag/ingestion.py ---------------------------------------------------------

def test_ingest_all_combines_pvpoke_and_mechanics_documents(monkeypatch):
    def fake_fetch_all_rankings(force_refresh=False):
        return {"great": GREAT_LEAGUE_SAMPLE, "ultra": ULTRA_LEAGUE_SAMPLE, "master": MASTER_LEAGUE_SAMPLE}

    monkeypatch.setattr(ingestion, "fetch_all_rankings", fake_fetch_all_rankings)

    documents = ingestion.ingest_all()

    sources = {doc.metadata["source"] for doc in documents}
    assert sources == {"pvpoke", "mechanics"}

    pvpoke_docs = [d for d in documents if d.metadata["source"] == "pvpoke"]
    mechanics_docs = [d for d in documents if d.metadata["source"] == "mechanics"]

    assert len(pvpoke_docs) == len(GREAT_LEAGUE_SAMPLE) + len(ULTRA_LEAGUE_SAMPLE) + len(MASTER_LEAGUE_SAMPLE)
    assert len(mechanics_docs) > 1  # the mechanics file is long enough to chunk into multiple pieces
    assert all(d.metadata["league"] == "all" for d in mechanics_docs)


def test_ingest_mechanics_loads_and_chunks_real_file():
    documents = ingestion.ingest_mechanics()

    assert len(documents) > 1
    assert all(d.metadata == {"source": "mechanics", "league": "all"} for d in documents)
    combined = " ".join(d.page_content for d in documents)
    assert "Shadow" in combined
    assert "stat_product" in combined or "stat product" in combined.lower()


# --- rag/store.py + rag/retriever.py ------------------------------------------

@pytest.fixture(scope="module")
def embeddings():
    return store.get_embeddings()


@pytest.fixture(scope="module")
def knowledge_store(tmp_path_factory, embeddings):
    great = GREAT_LEAGUE_SAMPLE + [
        _make_entry(
            "altaria", "Altaria", ["DRAGON_BREATH", "SKY_ATTACK", "DAZZLING_GLEAM"],
            [90.0, 60.0, 88.0, 50.0, 70.0, 94.0], 89.0,
        ),
    ]
    rankings = {"great": great, "ultra": ULTRA_LEAGUE_SAMPLE, "master": MASTER_LEAGUE_SAMPLE}
    documents = pvpoke.rankings_to_documents(rankings) + ingestion.ingest_mechanics()

    persist_path = str(tmp_path_factory.mktemp("chroma_store"))
    return store.build_store(documents, embeddings, persist_path)


@pytest.mark.parametrize("query", [
    "best great league team",
    "Medicham moveset",
    "raid counters",
])
def test_retrieval_returns_results_for_known_queries(knowledge_store, query):
    query_retriever = retriever.get_retriever(knowledge_store, k=4)
    results = query_retriever.invoke(query)

    assert len(results) > 0


def test_league_filter_restricts_results_to_one_league(knowledge_store):
    query_retriever = retriever.get_retriever(knowledge_store, k=10, league_filter="great")
    results = query_retriever.invoke("best Pokemon")

    assert len(results) > 0
    assert all(doc.metadata.get("league") == "great" for doc in results)


def test_search_returns_documents_with_scores(knowledge_store):
    results = retriever.search(knowledge_store, "Medicham moveset", k=3)

    assert len(results) > 0
    for doc, score in results:
        assert doc.page_content
        assert isinstance(score, float)


def test_has_relevant_context_true_for_on_topic_query(knowledge_store):
    assert retriever.has_relevant_context(
        knowledge_store, "Medicham moveset for Great League", threshold=0.3
    )


def test_has_relevant_context_false_for_nonsense_query(knowledge_store):
    assert not retriever.has_relevant_context(
        knowledge_store, "how to bake sourdough bread at high altitude", threshold=0.7
    )
