"""
The single shared state object that flows through every node in the graph.

Every node function receives the *current* state (or the fields it needs)
and returns a dict of the fields it wants to update. LangGraph merges that
dict back into the state before handing it to the next node. This is the
core mechanic that replaces "pass data via files + rerun each script" with
a real pipeline.
"""

from typing import TypedDict, Optional


class ResearchState(TypedDict, total=False):
    # ---- input ----
    topic: str

    # ---- planner node ----
    raw_files: list[str]
    subtopics_covered: list[str]
    subtopics_missing: list[str]
    planner_attempts: int

    # ---- cleaner node ----
    cleaned_files: list[str]

    # ---- merger node ----
    merged_report_md: str
    merged_report_path: str

    # ---- latex writer node ----
    latex_source: str
    latex_path: str

    # ---- latex compile node ----
    pdf_path: Optional[str]
    compile_success: bool
    compile_error: Optional[str]
    compile_attempts: int
