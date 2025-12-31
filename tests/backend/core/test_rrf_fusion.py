"""
Tests for RRF fusion algorithm.
"""

from src.backend.core.rrf_fusion import RRFFusion


def test_rrf_fusion_basic() -> None:
    """
    Test basic RRF fusion with both semantic and keyword results.
    """
    # Create RRF fusion instance
    rrf = RRFFusion(k=60)

    # Mock semantic results
    semantic_results = [
        {"noti_id": "NOTI-001", "text": "Semantic match 1"},
        {"noti_id": "NOTI-002", "text": "Semantic match 2"},
        {"noti_id": "NOTI-003", "text": "Semantic match 3"},
    ]

    # Mock keyword results
    keyword_results = [
        {"noti_id": "NOTI-002", "text": "Keyword match 1"},  # Overlap
        {"noti_id": "NOTI-004", "text": "Keyword match 2"},
    ]

    # Perform fusion
    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        semantic_weight=1.0,
        keyword_weight=1.0,
    )

    # Verify results
    assert isinstance(fused_results, list)
    assert len(fused_results) == 4  # 4 unique docs

    # Verify overlapping doc has higher score
    overlapping_doc = [r for r in fused_results if r["noti_id"] == "NOTI-002"][0]
    non_overlapping_doc = [r for r in fused_results if r["noti_id"] == "NOTI-001"][0]

    assert overlapping_doc["final_score"] > non_overlapping_doc["final_score"]

    # Verify ranking exists
    for result in fused_results:
        assert "rank" in result
        assert result["rank"] in range(1, 5)


def test_rrf_fusion_semantic_only() -> None:
    """
    Test RRF fusion with only semantic results.
    """
    rrf = RRFFusion(k=60)

    semantic_results = [
        {"noti_id": "NOTI-001", "text": "Result 1"},
        {"noti_id": "NOTI-002", "text": "Result 2"},
    ]

    keyword_results = []

    # Perform fusion
    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        semantic_weight=1.0,
        keyword_weight=1.0,
    )

    # Verify results
    assert len(fused_results) == 2
    assert fused_results[0]["rank"] == 1
    assert fused_results[1]["rank"] == 2

    # Verify all results have semantic_score > 0 and keyword_score = 0
    for result in fused_results:
        assert result["semantic_score"] > 0
        assert result["keyword_score"] == 0


def test_rrf_fusion_keyword_only() -> None:
    """
    Test RRF fusion with only keyword results.
    """
    rrf = RRFFusion(k=60)

    semantic_results = []

    keyword_results = [
        {"noti_id": "NOTI-001", "text": "Result 1"},
        {"noti_id": "NOTI-002", "text": "Result 2"},
    ]

    # Perform fusion
    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        semantic_weight=1.0,
        keyword_weight=1.0,
    )

    # Verify results
    assert len(fused_results) == 2
    assert fused_results[0]["rank"] == 1
    assert fused_results[1]["rank"] == 2

    # Verify all results have keyword_score > 0 and semantic_score = 0
    for result in fused_results:
        assert result["semantic_score"] == 0
        assert result["keyword_score"] > 0


def test_rrf_fusion_weighting() -> None:
    """
    Test RRF fusion with different weights.
    """
    rrf = RRFFusion(k=60)

    semantic_results = [
        {"noti_id": "NOTI-001", "text": "Semantic 1"},
        {"noti_id": "NOTI-002", "text": "Semantic 2"},
    ]

    keyword_results = [
        {"noti_id": "NOTI-001", "text": "Keyword 1"},
    ]

    # Perform fusion with semantic weight = 2.0, keyword weight = 0.5
    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        semantic_weight=2.0,
        keyword_weight=0.5,
    )

    # Verify weighting affects scores
    assert len(fused_results) == 2

    # Check semantic-only result has only semantic score
    semantic_only = [r for r in fused_results if r["noti_id"] == "NOTI-002"][0]
    assert semantic_only["semantic_score"] > semantic_only["keyword_score"]


def test_rrf_fusion_custom_k() -> None:
    """
    Test RRF fusion with custom k value.
    """
    rrf = RRFFusion(k=100)  # Larger k = lower scores

    semantic_results = [
        {"noti_id": "NOTI-001", "text": "Result 1"},
    ]

    keyword_results = []

    # Perform fusion
    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        semantic_weight=1.0,
        keyword_weight=1.0,
    )

    # Verify score is lower with larger k
    score = fused_results[0]["final_score"]
    # Score = 1 / (100 + 1) ≈ 0.0099
    assert 0 < score < 0.1


def test_rrf_fusion_empty_results() -> None:
    """
    Test RRF fusion with no results.
    """
    rrf = RRFFusion(k=60)

    semantic_results = []
    keyword_results = []

    # Perform fusion
    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        semantic_weight=1.0,
        keyword_weight=1.0,
    )

    # Verify empty results
    assert len(fused_results) == 0


def test_rrf_score_calculation() -> None:
    """
    Verify RRF score calculation formula: score = 1 / (k + rank) * weight
    """
    rrf = RRFFusion(k=60)

    semantic_results = [
        {"noti_id": "NOTI-001", "text": "Rank 1"},
        {"noti_id": "NOTI-002", "text": "Rank 2"},
    ]

    fused_results = rrf.fuse(
        semantic_results=semantic_results,
        keyword_results=[],
        semantic_weight=1.0,
        keyword_weight=1.0,
    )

    # Rank 1 score = 1 / (60 + 1) * 1.0 = 1/61 ≈ 0.0164
    # Rank 2 score = 1 / (60 + 2) * 1.0 = 1/62 ≈ 0.0161
    rank1_score = fused_results[0]["semantic_score"]
    rank2_score = fused_results[1]["semantic_score"]

    assert 0.016 < rank1_score < 0.017
    assert 0.016 < rank2_score < 0.017
    assert rank1_score > rank2_score  # Rank 1 should have higher score
