"""
Builds the LangGraph StateGraph for the whole pipeline:
    planner --(retry loop until subtopics complete)--> cleaner
    cleaner -> merger -> latex_writer -> latex_compile
    latex_compile --(fix loop, up to 3 tries)--> fix_latex -> latex_compile
    latex_compile --(success, or gave up)--> END
"""
import sqlite3
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from graph.state import ResearchState
from graph.router import route_after_planner, route_after_compile
from nodes.planner_node import planner_node
from nodes.cleaner_node import cleaner_node
from nodes.merger_node import merger_node
from nodes.latex_writer_node import latex_writer_node
from nodes.latex_compile_node import latex_compile_node, fix_latex_node
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_DB = PROJECT_ROOT / "checkpoints" / "pipeline.db"

def build_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("cleaner", cleaner_node)
    workflow.add_node("merger", merger_node)
    workflow.add_node("latex_writer", latex_writer_node)
    workflow.add_node("latex_compile", latex_compile_node)
    workflow.add_node("fix_latex", fix_latex_node)

    workflow.add_edge(START, "planner")

    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {"retry": "planner", "continue": "cleaner"},
    )

    workflow.add_edge("cleaner", "merger")
    workflow.add_edge("merger", "latex_writer")
    workflow.add_edge("latex_writer", "latex_compile")

    workflow.add_conditional_edges(
        "latex_compile",
        route_after_compile,
        {"fix": "fix_latex", "done": END, "give_up": END},
    )
    workflow.add_edge("fix_latex", "latex_compile")

    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    checkpointer = SqliteSaver(checkpoint_conn)

    return workflow.compile(checkpointer=checkpointer)
