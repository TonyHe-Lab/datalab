"""
Reciprocal Rank Fusion (RRF) algorithm for combining search results.
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RRFFusion:
    """Reciprocal Rank Fusion for combining search results from multiple sources."""

    def __init__(self, k: int = 60):
        """
        Initialize RRF fusion.

        Args:
            k: Constant for RRF calculation (default: 60)
        """
        self.k = k

    def fuse(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        semantic_weight: float = 1.0,
        keyword_weight: float = 1.0,
    ) -> List[Dict]:
        """
        Fuse semantic and keyword search results using RRF.

        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            semantic_weight: Weight for semantic search results
            keyword_weight: Weight for keyword search results

        Returns:
            Fused and ranked results
        """
        # Calculate RRF scores for each result
        doc_scores = {}

        # Process semantic results
        for idx, result in enumerate(semantic_results, start=1):
            doc_id = result["noti_id"]
            # RRF score: 1 / (k + rank) * weight
            semantic_score = (1.0 / (self.k + idx)) * semantic_weight

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    **result,
                    "semantic_rank": idx,
                    "keyword_rank": None,
                    "semantic_score": semantic_score,
                    "keyword_score": 0.0,
                    "final_score": semantic_score,
                }
            else:
                doc_scores[doc_id]["semantic_rank"] = idx
                doc_scores[doc_id]["semantic_score"] = semantic_score
                doc_scores[doc_id]["final_score"] += semantic_score

        # Process keyword results
        for idx, result in enumerate(keyword_results, start=1):
            doc_id = result["noti_id"]
            # RRF score: 1 / (k + rank) * weight
            keyword_score = (1.0 / (self.k + idx)) * keyword_weight

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    **result,
                    "semantic_rank": None,
                    "keyword_rank": idx,
                    "semantic_score": 0.0,
                    "keyword_score": keyword_score,
                    "final_score": keyword_score,
                }
            else:
                doc_scores[doc_id]["keyword_rank"] = idx
                doc_scores[doc_id]["keyword_score"] = keyword_score
                doc_scores[doc_id]["final_score"] += keyword_score

        # Sort by final score
        fused_results = sorted(
            doc_scores.values(),
            key=lambda x: x["final_score"],
            reverse=True,
        )

        # Add rank to fused results
        for idx, result in enumerate(fused_results, start=1):
            result["rank"] = idx

        logger.info(
            f"RRF fusion: {len(semantic_results)} semantic + "
            f"{len(keyword_results)} keyword = {len(fused_results)} fused"
        )

        return fused_results

    def deduplicate(self, results: List[Dict]) -> List[Dict]:
        """
        Deduplicate search results by notification ID.

        Args:
            results: List of search results

        Returns:
            Deduplicated results
        """
        seen = set()
        deduplicated = []

        for result in results:
            doc_id = result.get("noti_id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                deduplicated.append(result)

        logger.info(f"Deduplicated {len(results)} results to {len(deduplicated)}")
        return deduplicated
