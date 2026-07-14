"""
Compiles a .tex file into a .pdf.

Tries `tectonic` first (self-contained, no system LaTeX install needed,
auto-fetches packages on first run). Falls back to `pdflatex` (run twice,
so \\tableofcontents resolves correctly) if tectonic isn't installed.
"""

import shutil
import subprocess
from pathlib import Path
from langchain_core.tools import tool


def _run(cmd: list[str], cwd: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


@tool
def compile_latex(tex_path: str, output_dir: str) -> dict:
    """
    Compile a .tex file into a PDF.

    Args:
        tex_path: Path to the .tex source file.
        output_dir: Directory to write the .pdf (and build artifacts) into.

    Returns a dict: {success: bool, pdf_path: str|None, log: str}
    """
    tex_path = Path(tex_path).resolve()
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)
    stem = tex_path.stem

    if shutil.which("tectonic"):
        result = _run(
            ["tectonic", "--outdir", str(output_dir_path), tex_path.name],
            cwd=str(tex_path.parent),
        )
        pdf_path = output_dir_path / f"{stem}.pdf"
        return {
            "success": pdf_path.exists() and result.returncode == 0,
            "pdf_path": str(pdf_path) if pdf_path.exists() else None,
            "log": (result.stdout + "\n" + result.stderr)[-4000:],
        }

    if shutil.which("pdflatex"):
        result = None
        for _ in range(2):  # run twice so the table of contents resolves
            result = _run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory", str(output_dir_path),
                    tex_path.name,
                ],
                cwd=str(tex_path.parent),
            )
        pdf_path = output_dir_path / f"{stem}.pdf"
        return {
            "success": pdf_path.exists() and result.returncode == 0,
            "pdf_path": str(pdf_path) if pdf_path.exists() else None,
            "log": result.stdout[-4000:],
        }

    return {
        "success": False,
        "pdf_path": None,
        "log": (
            "No LaTeX engine found on PATH. Install either:\n"
            "  - tectonic (https://tectonic-typesetting.github.io), or\n"
            "  - a TeX distribution providing pdflatex "
            "(TeX Live / MiKTeX / MacTeX)."
        ),
    }
