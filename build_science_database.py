import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path
from typing import Any

from distillation_policy import should_distill
from source_spans import validate_claims_against_cards


ROOT = Path(__file__).parent
DEFAULT_SOURCES = (
    ("data/maude_2018_cart.json", "data/maude_2018_claims.json"),
    ("data/neelapu_2017_axi_cel.json", "data/neelapu_2017_claims.json"),
)
DEFAULT_OUTPUT = "data/science_claim_audit_db.json"


class AuditGraphState:
    def __init__(self) -> None:
        self.trusted_claims: list[dict[str, Any]] = []

    def has_duplicate(self, claim: dict[str, Any]) -> bool:
        return any(existing.get("text") == claim.get("text") for existing in self.trusted_claims)

    def has_conflict(self, claim: dict[str, Any]) -> bool:
        if claim.get("direction") != "improves":
            return False
        return any(
            existing.get("kind") == "negative_result"
            and existing.get("outcome") == claim.get("outcome")
            for existing in self.trusted_claims
        )

    def remember_if_promoted(self, claim: dict[str, Any], promote: bool) -> None:
        if promote:
            self.trusted_claims.append(dict(claim))


def build_database(sources: list[tuple[Path, Path]]) -> dict[str, Any]:
    graph = AuditGraphState()
    papers: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for cards_path, claims_path in sources:
        cards = _read_json(cards_path)
        claims = _read_json(claims_path)
        issues = validate_claims_against_cards(claims, cards)
        if issues:
            detail = "\n".join(f"- {issue.code}: {issue.claim_id}: {issue.message}" for issue in issues)
            raise RuntimeError(f"{claims_path} failed provenance validation:\n{detail}")

        for card in cards:
            papers.append(_paper_summary(card))

        for claim in claims:
            decision = should_distill(claim, graph)
            graph.remember_if_promoted(claim, decision.promote)
            records.append(_audit_record(claim, decision))

    summary = _summary(papers, records)
    return {
        "database_name": "hypothesis_wiki_science_claim_audit_db",
        "version": 1,
        "description": (
            "A small real-paper claim audit database: CAR-T trial claims with "
            "PubMed/DOI provenance, verbatim evidence spans, scope conditions, "
            "safety-risk flags, and distillation-gate promotion decisions."
        ),
        "summary": summary,
        "source_papers": papers,
        "demo_queries": [
            {
                "id": "car_t_efficacy_safety",
                "query": "What efficacy and safety claims are supported for the CAR-T trials?",
                "expected_behavior": (
                    "Return efficacy claims with trial scope, and include safety-risk "
                    "claims instead of only reporting response rates."
                ),
            },
            {
                "id": "car_t_safety_audit",
                "query": "Which promoted CAR-T claims are safety risks?",
                "expected_behavior": "Return CRS, neurologic events, cytopenias, adverse events, and deaths.",
            },
        ],
        "records": records,
    }


def write_database(database: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(database, indent=2, ensure_ascii=True) + "\n")


async def load_live(database: dict[str, Any], session_id: str) -> dict[str, Any]:
    from backend.storage import create_memory_backend

    backend = await create_memory_backend()
    promoted = 0
    for record in database["records"]:
        await backend.remember(record, session_id=session_id)
        if record["promotion_status"] == "promote":
            decision = await backend.promote_candidate(record["claim"])
            promoted += int(decision.promote)
    return {
        "session_backend": backend.session_store.__class__.__name__,
        "trusted_graph_backend": backend.trusted_graph.__class__.__name__,
        "session_records_written": len(database["records"]),
        "claims_promoted": promoted,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the real science claim audit database.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--load-live",
        action="store_true",
        help="Also write records through Redis and promote claims into Cognee.",
    )
    parser.add_argument("--session-id", default="science-claim-audit-db")
    args = parser.parse_args()

    sources = [(ROOT / cards, ROOT / claims) for cards, claims in DEFAULT_SOURCES]
    database = build_database(sources)
    output_path = ROOT / args.output
    write_database(database, output_path)
    _print_summary(database, output_path)

    if args.load_live:
        live = asyncio.run(load_live(database, args.session_id))
        print()
        print("live_load:")
        for key, value in live.items():
            print(f"  {key}: {value}")


def _audit_record(claim: dict[str, Any], decision) -> dict[str, Any]:
    return {
        "claim_id": claim["id"],
        "paper_id": claim["source"],
        "paper_title": claim["paper_title"],
        "source_url": claim["source_url"],
        "doi": claim["doi"],
        "pmid": claim.get("pmid"),
        "kind": claim["kind"],
        "audit_verdict": _audit_verdict(claim),
        "text": claim["text"],
        "outcome": claim["outcome"],
        "direction": claim["direction"],
        "scope_conditions": claim["scope_conditions"],
        "evidence_span": claim["evidence_span"],
        "evidence_start": claim["evidence_start"],
        "evidence_end": claim["evidence_end"],
        "evidence_span_valid": claim["evidence_span_valid"],
        "confidence": claim["confidence"],
        "promotion_status": decision.status,
        "promotion_reason": decision.reason,
        "promotion_confidence": decision.confidence,
        "trusted_graph_ready": decision.promote,
        "claim": claim,
    }


def _audit_verdict(claim: dict[str, Any]) -> str:
    if claim.get("kind") == "negative_result" or claim.get("direction") == "safety_risk":
        return "safety_risk"
    if claim.get("kind") == "hypothesis" and claim.get("direction") == "improves":
        return "supported_efficacy"
    return "supporting_evidence"


def _paper_summary(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_id": card["paper_id"],
        "title": card["title"],
        "year": card.get("year"),
        "journal": card.get("journal"),
        "doi": card.get("doi"),
        "pmid": card.get("pmid"),
        "pmcid": card.get("pmcid"),
        "url": card.get("url"),
        "source_type": card.get("source_type"),
    }


def _summary(papers: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    verdicts = Counter(record["audit_verdict"] for record in records)
    promotions = Counter(record["promotion_status"] for record in records)
    return {
        "paper_count": len(papers),
        "claim_count": len(records),
        "provenance_valid_claims": sum(1 for record in records if record["evidence_span_valid"]),
        "trusted_graph_ready_claims": sum(1 for record in records if record["trusted_graph_ready"]),
        "safety_risk_claims": verdicts["safety_risk"],
        "supported_efficacy_claims": verdicts["supported_efficacy"],
        "supporting_evidence_claims": verdicts["supporting_evidence"],
        "promotion_status_counts": dict(sorted(promotions.items())),
        "audit_verdict_counts": dict(sorted(verdicts.items())),
    }


def _print_summary(database: dict[str, Any], output_path: Path) -> None:
    summary = database["summary"]
    print(f"database: {output_path.relative_to(ROOT)}")
    print(f"papers:   {summary['paper_count']}")
    print(f"claims:   {summary['claim_count']}")
    print(f"valid:    {summary['provenance_valid_claims']}")
    print(f"promote:  {summary['trusted_graph_ready_claims']}")
    print(f"safety:   {summary['safety_risk_claims']}")
    print(f"efficacy: {summary['supported_efficacy_claims']}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


if __name__ == "__main__":
    main()
