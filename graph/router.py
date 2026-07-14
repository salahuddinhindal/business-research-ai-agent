"""
Conditional-edge functions. Each one inspects the current state and returns
a string key that graph/builder.py maps to the next node. This is the part
that a linear script (your original main.py) simply cannot express.
"""
from graph.state import ResearchState
MAX_PLANNER_ATTEMPTS = 2
MAX_COMPILE_ATTEMPTS = 3
def route_after_planner(state: ResearchState) -> str:
    still_missing = state.get("subtopics_missing", [])
    attempts = state.get("planner_attempts", 0)
    if still_missing and attempts < MAX_PLANNER_ATTEMPTS:
        return "retry"
    return "continue"
def route_after_compile(state: ResearchState) -> str:
    if state.get("compile_success"):
        return "done"
    if state.get("compile_attempts", 0) >= MAX_COMPILE_ATTEMPTS:
        return "give_up"
    return "fix"
