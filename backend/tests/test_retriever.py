def test_loads_all_documents(retriever):
    assert retriever.document_count == 9


def test_rejection_query_ranks_rejection_doc_first(retriever):
    results = retriever.search("my claim was rejected and I do not understand why")
    assert results
    assert results[0].doc_id == "claim-rejection-reasons"


def test_coverage_query_finds_coverage_doc(retriever):
    results = retriever.search("is flood damage covered on my policy")
    assert "coverage-details" in [r.doc_id for r in results]


def test_empty_query_returns_nothing(retriever):
    assert retriever.search("") == []
    assert retriever.search("the a of") == []


def test_top_k_limits_results(retriever):
    assert len(retriever.search("claim", top_k=2)) <= 2
