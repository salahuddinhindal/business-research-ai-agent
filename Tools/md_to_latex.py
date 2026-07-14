"""
Markdown -> LaTeX converter.

This is a deterministic parser (no LLM involved) — same philosophy as the
original Tools/md_to_docx.py, just emitting LaTeX markup instead of
python-docx calls. Deterministic on purpose: formatting/escaping is not a
task you want an LLM improvising on, since a single unescaped '&' or '_'
breaks the whole PDF compile.
"""

import re
from pathlib import Path
from langchain_core.tools import tool

# ---------- Escaping ----------

_LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in plain text (not markdown syntax)."""
    # Backslash must be handled first so we don't double-escape our own output.
    result = []
    for ch in text:
        result.append(_LATEX_SPECIAL_CHARS.get(ch, ch))
    return "".join(result)


def convert_inline(text: str) -> str:
    """
    Convert **bold**, *italic*/_italic_ and inline `code` to LaTeX,
    escaping everything else. Markdown link syntax [text](url) is converted
    to \\href{url}{text}.
    """
    # Links first, since they contain characters (like _) that must not be
    # escaped inside the URL.
    def link_sub(m):
        label = escape_latex(m.group(1))
        url = m.group(2).replace("%", r"\%").replace("#", r"\#")
        return r"\href{%s}{%s}" % (url, label)

    text = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", link_sub, text)

    # Split on bold / italic / inline-code markers while keeping delimiters.
    tokens = re.split(r"(\*\*.+?\*\*|`.+?`|\*.+?\*|_.+?_)", text)

    out = []
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            out.append(r"\textbf{%s}" % escape_latex(token[2:-2]))
        elif token.startswith("`") and token.endswith("`"):
            out.append(r"\texttt{%s}" % escape_latex(token[1:-1]))
        elif (token.startswith("*") and token.endswith("*")) or \
             (token.startswith("_") and token.endswith("_")):
            out.append(r"\textit{%s}" % escape_latex(token[1:-1]))
        else:
            # already-inserted \href{...}{...} must pass through untouched
            if r"\href{" in token:
                out.append(token)
            else:
                out.append(escape_latex(token))
    return "".join(out)


# ---------- Table parsing ----------

def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_table_separator(line: str) -> bool:
    stripped = line.strip().strip("|")
    cells = [c.strip() for c in stripped.split("|")]
    return len(cells) > 0 and all(re.fullmatch(r":?-+:?", c) for c in cells)


def parse_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    n_cols = len(rows[0])
    col_spec = "l" * n_cols
    lines = [r"\begin{longtable}{%s}" % col_spec, r"\toprule"]

    header = rows[0]
    lines.append(" & ".join(r"\textbf{%s}" % convert_inline(c) for c in header) + r" \\")
    lines.append(r"\midrule")

    for row in rows[1:]:
        cells = row + [""] * (n_cols - len(row))
        lines.append(" & ".join(convert_inline(c) for c in cells[:n_cols]) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    return "\n".join(lines)


# ---------- Main parser ----------

HEADING_CMD = {1: "section", 2: "subsection", 3: "subsubsection", 4: "paragraph"}


def markdown_to_latex_body(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    i, n = 0, len(lines)
    out = []
    list_stack = []  # tracks open \begin{itemize}/\begin{enumerate}

    def close_lists():
        while list_stack:
            out.append(r"\end{%s}" % list_stack.pop())

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            close_lists()
            i += 1
            continue

        # Horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            close_lists()
            out.append(r"\noindent\rule{\linewidth}{0.4pt}")
            i += 1
            continue

        # Heading
        heading_match = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if heading_match:
            close_lists()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            cmd = HEADING_CMD.get(level, "paragraph")
            out.append(r"\%s{%s}" % (cmd, convert_inline(text)))
            i += 1
            continue

        # Table
        if is_table_row(line) and i + 1 < n and is_table_separator(lines[i + 1]):
            close_lists()
            table_rows = [parse_table_row(line)]
            i += 2
            while i < n and is_table_row(lines[i]):
                table_rows.append(parse_table_row(lines[i]))
                i += 1
            out.append(render_table(table_rows))
            continue

        # Numbered list
        numbered_match = re.match(r"^\d+\.\s+(.*)", stripped)
        if numbered_match:
            if not list_stack or list_stack[-1] != "enumerate":
                close_lists()
                out.append(r"\begin{enumerate}")
                list_stack.append("enumerate")
            out.append(r"\item %s" % convert_inline(numbered_match.group(1)))
            i += 1
            continue

        # Bullet list
        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            if not list_stack or list_stack[-1] != "itemize":
                close_lists()
                out.append(r"\begin{itemize}")
                list_stack.append("itemize")
            out.append(r"\item %s" % convert_inline(bullet_match.group(1)))
            i += 1
            continue

        # Default paragraph
        close_lists()
        out.append(convert_inline(stripped))
        i += 1

    close_lists()
    return "\n\n".join(out)


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "report_template.tex"


@tool
def md_to_latex(input_file: str, output_file: str, title: str = "Business Research Report") -> str:
    """
    Convert a Markdown (.md) file into a complete, compilable LaTeX (.tex)
    document using templates/report_template.tex as the wrapper (preamble,
    title page, table of contents).

    Args:
        input_file: Path to the Markdown file to convert.
        output_file: Path where the .tex file should be saved.
        title: Report title used on the title page.
    """
    from datetime import date

    with open(input_file, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    body = markdown_to_latex_body(markdown_text)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    latex_source = (
        template
        .replace("%%TITLE%%", escape_latex(title))
        .replace("%%DATE%%", date.today().strftime("%B %d, %Y"))
        .replace("%%BODY%%", body)
    )

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex_source)

    return f"LaTeX source saved to: {output_file}"
