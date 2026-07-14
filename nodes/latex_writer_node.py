from pathlib import Path

from Tools.md_to_latex import md_to_latex
from graph.state import ResearchState

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINAL_REPORTS_DIR = PROJECT_ROOT / "data" / "final_reports"
LATEX_PATH = FINAL_REPORTS_DIR / "business_report.tex"


def latex_writer_node(state: ResearchState) -> dict:
    """
    Converts merged_report.md into a full .tex document.

    This is deliberately a direct function call, not an LLM agent step:
    markdown->LaTeX formatting/escaping is a mechanical transformation,
    and letting an LLM "rewrite" LaTeX risks introducing unescaped
    characters that silently break the PDF compile later.
    """
    merged_path = state.get("merged_report_path")
    if not merged_path or not Path(merged_path).exists():
        return {"latex_source": "", "latex_path": ""}

    topic = state.get("topic", "Business Research Report")
    title = f"{topic.strip().title()} — Business Research Report"

    FINAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # md_to_latex is a LangChain @tool, so it's called via .invoke() with a dict
    md_to_latex.invoke({
        "input_file": merged_path,
        "output_file": str(LATEX_PATH),
        "title": title,
    })

    with open(LATEX_PATH, "r", encoding="utf-8") as f:
        latex_source = f.read()

    return {
        "latex_source": latex_source,
        "latex_path": str(LATEX_PATH),
    }
