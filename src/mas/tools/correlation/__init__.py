"""Tools used by the correlation agent."""

from mas.tools.correlation.query_incidents import query_known_incidents
from mas.tools.correlation.signatures import extract_signatures

__all__ = [
    "extract_signatures",
    "query_known_incidents",
]
