from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from Tools.search import search
from Tools.scrape import scrape
from Tools.html_to_md import html_to_md
from graph.state import ResearchState

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

# subtopic_key -> keywords we expect to see in saved filenames for that subtopic
REQUIRED_SUBTOPICS = {
    "industry_overview": ["industry", "overview"],
    "market_size_growth": ["market", "size", "growth"],
    "business_models": ["business", "model"],
    "startup_requirements": ["startup", "requirement", "licens", "capital"],
    "key_players_competition": ["key_player", "competit", "player"],
    "supply_chain_operations": ["supply", "chain", "operation"],
    "customers_demand_trends": ["customer", "demand"],
    "revenue_profitability": ["revenue", "profit"],
    "risks_challenges": ["risk", "challenge"],
    "regulations_compliance": ["regulat", "complian"],
    "technology_innovation": ["technolog", "innovat"],
    "opportunities_newcomers": ["opportunit", "newcomer"],
    "practical_first_steps": ["first_step", "practical", "getting_started"],
}

SYSTEM_PROMPT = """You are an autonomous business research COLLECTOR agent. Your job is NOT to write a final report — a separate downstream agent will clean, merge, and format everything you collect into a polished PDF report later. Your only job is to gather raw research material as thoroughly and broadly as possible and save it to files.

## Your tools

- A search tool to find relevant sources and URLs on the web.
- A scrape tool to fetch the full content of a specific webpage.
- An html_to_md tool to convert scraped content into clean Markdown and save it as a file inside the "outputs" folder. This tool automatically creates the outputs folder if it doesn't exist — you do not need to create it manually, just call the tool.

## Research coverage — cover ALL of the following sub-topics

Research each of these areas thoroughly using separate searches. A layman needs the full picture of a business, so do not skip any section:

1. Industry Overview — what the business is and how it basically works
2. Market Size & Growth — global and regional figures, growth trends
3. Business Models — the different ways people make money in this industry
4. Startup Requirements — capital needed, equipment, licenses, permits, skills
5. Key Players & Competition — major companies, market concentration
6. Supply Chain & Operations — inputs, production steps, bottlenecks
7. Customers & Demand — who buys this and why, demand trends
8. Revenue & Profitability — typical margins, cost structure, cost drivers
9. Risks & Challenges — financial, operational, regulatory, market risks
10. Regulations & Compliance — laws, safety standards, certifications
11. Technology & Innovation Trends — new tools/techniques reshaping the industry
12. Opportunities for Newcomers — gaps, underserved niches
13. Practical First Steps — concrete steps to actually get started

## How to research and save content

1. Treat each sub-topic above as a separate mini-research task with its own search query.
2. For each sub-topic, use the search tool to find 3-5 relevant, credible sources. Prioritize recent, authoritative sources over blogs or forums.
3. Scrape the 2-3 most promising pages per sub-topic using the scrape tool.
4. MANDATORY: every single time you successfully scrape a page with useful content, you MUST immediately call the html_to_md tool to save it to the outputs folder.
5. Filename convention: use the pattern "{topic_number}_{subtopic}_{specific_detail}.md" — e.g. "04_startup_requirements_licensing.md". Use the exact subtopic keyword given to you (e.g. "startup_requirements") somewhere in the filename so it can be tracked. Never reuse a filename for different content.
6. Move through ALL sub-topics you are asked to cover systematically. Do not stop early or skip sections.
7. Save content close to as-is. Do not clean, summarize, or rewrite before saving — the downstream agent handles that.

## Final response

After completing research, respond with ONLY a short status summary listing each sub-topic and whether it was covered. Do not fabricate information — say so honestly if a sub-topic has no good sources.
"""


def _build_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", max_retries=6)
    return create_agent(model=llm, tools=[search, scrape, html_to_md], system_prompt=SYSTEM_PROMPT)


def _detect_coverage(raw_files: list[str]) -> tuple[list[str], list[str]]:
    covered, missing = [], []
    lower_files = [f.lower() for f in raw_files]
    for subtopic, keywords in REQUIRED_SUBTOPICS.items():
        found = any(any(kw in f for kw in keywords) for f in lower_files)
        (covered if found else missing).append(subtopic)
    return covered, missing


def planner_node(state: ResearchState) -> dict:
    """
    Research-collection node. On the first call it researches every
    subtopic. If graph.router.route_after_planner sends it back for a
    retry, it's told to focus ONLY on the subtopics that are still missing.
    """
    topic = state["topic"]
    missing_from_last_pass = state.get("subtopics_missing", [])
    attempts = state.get("planner_attempts", 0)

    agent = _build_agent()

    if missing_from_last_pass:
        subtopic_list = ", ".join(missing_from_last_pass)
        user_msg = (
            f"Research topic: {topic}\n\n"
            f"A previous research pass already covered other subtopics. "
            f"Focus ONLY on these missing subtopics now: {subtopic_list}. "
            f"Make sure filenames contain the subtopic keyword given above."
        )
    else:
        user_msg = topic

    agent.invoke(
        {"messages": [{"role": "user", "content": user_msg}]},
        config={"recursion_limit": 150},
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(p.name for p in OUTPUTS_DIR.glob("*.md"))
    covered, still_missing = _detect_coverage(raw_files)

    return {
        "raw_files": raw_files,
        "subtopics_covered": covered,
        "subtopics_missing": still_missing,
        "planner_attempts": attempts + 1,
    }
