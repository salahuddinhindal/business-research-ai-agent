from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from Tools.latex_compiler import compile_latex
from graph.state import ResearchState

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINAL_REPORTS_DIR = PROJECT_ROOT / "data" / "final_reports"
BUILD_DIR = FINAL_REPORTS_DIR / "latex_build"


def latex_compile_node(state: ResearchState) -> dict:
    """Runs the LaTeX engine on latex_path and records success/failure."""
    latex_path = state.get("latex_path")
    attempts = state.get("compile_attempts", 0)

    if not latex_path or not Path(latex_path).exists():
        return {"compile_success": False, "compile_error": "No .tex file to compile.",
                "compile_attempts": attempts + 1}

    result = compile_latex.invoke({"tex_path": latex_path, "output_dir": str(BUILD_DIR)})

    pdf_path = None
    if result["success"]:
        # copy final pdf next to the .tex for a clean deliverable path
        built_pdf = Path(result["pdf_path"])
        final_pdf = FINAL_REPORTS_DIR / built_pdf.name
        final_pdf.write_bytes(built_pdf.read_bytes())
        pdf_path = str(final_pdf)

    return {
        "compile_success": result["success"],
        "compile_error": None if result["success"] else result["log"],
        "pdf_path": pdf_path,
        "compile_attempts": attempts + 1,
    }


FIX_SYSTEM_PROMPT = """You are a LaTeX debugging specialist.
You will be given a full .tex source file and the error log produced by
the LaTeX compiler. Find the specific line(s) causing the failure (unescaped
special characters, unclosed environments, malformed table rows, etc.) and
fix ONLY what is necessary to make it compile.

Rules:
- Return the COMPLETE corrected .tex file, nothing else.
- Do not remove content, sections, or data — only fix syntax.
- Do not add explanations, markdown fences, or commentary before/after the code.
"""


def fix_latex_node(state: ResearchState) -> dict:
    """LLM-based repair step, only reached if compilation failed."""
    latex_source = state.get("latex_source", "")
    error_log = state.get("compile_error", "")

    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    user_msg = (
        f"Compiler error log:\n{error_log}\n\n"
        f"Broken .tex source:\n{latex_source}"
    )
    response = llm.invoke([
        {"role": "system", "content": FIX_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])

    fixed_source = response.content.strip()
    # strip stray markdown fences if the model added them despite instructions
    if fixed_source.startswith("```"):
        fixed_source = fixed_source.strip("`")
        fixed_source = fixed_source.split("\n", 1)[1] if "\n" in fixed_source else fixed_source

    latex_path = state.get("latex_path")
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(fixed_source)

    return {"latex_source": fixed_source}
