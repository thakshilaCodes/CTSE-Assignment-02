"""Correlation stage pipeline: derive signatures and map to known incident classes."""

from __future__ import annotations

from collections import Counter

from mas.agents.correlation.report import CorrelationReport
from mas.core.observability import log_agent_step, log_tool_invocation
from mas.tools.correlation import extract_signatures, query_known_incidents


def _score_match(match: dict[str, str]) -> int:
    source = match.get("source", "")
    severity = match.get("severity", "").lower()
    score = 10 if source == "sqlite" else 6
    if severity == "critical":
        score += 4
    elif severity == "high":
        score += 3
    elif severity == "medium":
        score += 1
    return score


def _derive_candidate_class(matches_by_signature: dict[str, list[dict[str, str]]]) -> tuple[str, str]:
    if not matches_by_signature:
        return "UNKNOWN", "low"

    class_scores: Counter[str] = Counter()
    total_matches = 0
    sqlite_hits = 0
    for matches in matches_by_signature.values():
        for match in matches:
            total_matches += 1
            if match.get("source") == "sqlite":
                sqlite_hits += 1
            klass = match.get("incident_class", "UNKNOWN") or "UNKNOWN"
            class_scores[klass] += _score_match(match)

    if not class_scores:
        return "UNKNOWN", "low"

    candidate, top_score = class_scores.most_common(1)[0]
    runner_up = class_scores.most_common(2)[1][1] if len(class_scores) > 1 else 0
    margin = top_score - runner_up

    if sqlite_hits >= 2 and margin >= 4:
        confidence = "high"
    elif total_matches >= 2 and margin >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    return candidate, confidence


def run_correlation_pipeline(
    *,
    ingest_findings: str,
    db_path: str | None = None,
    max_signatures: int = 8,
    max_matches_per_signature: int = 5,
) -> CorrelationReport:
    """
    Build correlation findings from ingest output.

    Steps:
    1) extract signatures from ingest text
    2) query local incident knowledge per signature
    3) compute candidate incident class and confidence
    4) emit deterministic markdown for ``GlobalState['correlation_findings']``
    """
    signatures = extract_signatures(ingest_findings, limit=max_signatures)
    matches_by_signature: dict[str, list[dict[str, str]]] = {}

    for signature in signatures:
        matches = query_known_incidents(
            signature,
            limit=max_matches_per_signature,
            db_path=db_path,
        )
        log_tool_invocation(
            "query_known_incidents",
            {"signature": signature, "limit": max_matches_per_signature, "db_path": db_path or ""},
            str(matches),
        )
        if matches:
            matches_by_signature[signature] = matches

    candidate_class, confidence = _derive_candidate_class(matches_by_signature)

    lines: list[str] = [
        "## Correlation findings",
        "",
        "### Candidate incident class",
        "",
        f"- Class: `{candidate_class}`",
        f"- Confidence: `{confidence}`",
        "",
        "### Signatures extracted from ingest",
        "",
    ]
    if signatures:
        for sig in signatures:
            lines.append(f"- `{sig}`")
    else:
        lines.append("- (none extracted)")

    lines.extend(["", "### Matched incidents", ""])
    if matches_by_signature:
        for sig, matches in matches_by_signature.items():
            lines.append(f"#### Signature: `{sig}`")
            for m in matches:
                lines.append(
                    "- "
                    f"[{m.get('source', 'unknown')}] "
                    f"{m.get('title', 'Untitled')} | class={m.get('incident_class', 'UNKNOWN')} "
                    f"| severity={m.get('severity', 'unknown')} "
                    f"| resolution={m.get('resolution', '')}"
                )
            lines.append("")
    else:
        lines.append("- No historical incidents matched. Consider collecting more incident history.")

    summary = "\n".join(lines).strip()
    report = CorrelationReport(
        signatures=signatures,
        matches_by_signature=matches_by_signature,
        candidate_incident_class=candidate_class,
        confidence=confidence,
        summary_markdown=summary,
    )
    log_agent_step(
        "correlation",
        {
            "signatures": len(signatures),
            "matched_signatures": len(matches_by_signature),
            "candidate_incident_class": candidate_class,
            "confidence": confidence,
        },
    )
    return report
