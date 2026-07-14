# Autonomous Business Research Agent --- Lang Graph Edition

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-green)
![LangChain](https://img.shields.io/badge/LangChain-Framework-brightgreen)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-yellow)
![GitHub stars](https://img.shields.io/github/stars/Abdullah9712/BusinessResearchAgentLangGraph?style=social)
![GitHub forks](https://img.shields.io/github/forks/Abdullah9712/BusinessResearchAgentLangGraph?style=social)

An **Agentic AI system** built with **LangGraph** that autonomously researches a business topic, gathers information from the web, cleans and organizes the data, and generates a professional **LaTeX-based PDF report**.

---

# Overview

Traditional business research requires manually searching multiple websites, organizing information, and writing reports.

This project automates the entire workflow using a **stateful multi-agent architecture** built with LangGraph.

The system:

1. Researches a business topic.
2. Collects information from multiple web sources.
3. Cleans noisy content.
4. Merges findings into a structured report.
5. Converts the report into LaTeX.
6. Generates a professional PDF.
7. Automatically recovers from research gaps and LaTeX failures.

---

# Features

 Autonomous Web Research

 Multi-Agent Workflow using LangGraph

 State-Based Execution Pipeline

 Conditional Routing and Retry Loops

 Self-Healing LaTeX Compilation

 Automatic Data Cleaning

 Markdown → PDF Report Generation

 SQLite Checkpointing and Resumability

 Modular and Extensible Architecture

---

# System Architecture

```text
START
   │
   ▼
┌───────────┐
│ Planner   │
└─────┬─────┘
      │
      │ Missing Topics?
      ├───────────────Yes──────────────────┐
      │                                     │
      │                                     ▼
      │                             Retry Planner
      │                              (Max 2x)
      │                                     │
      └──────────────No─────────────────────┘
                      │
                      ▼
              ┌───────────┐
              │ Cleaner   │
              └────┬──────┘
                   │
                   ▼
              ┌───────────┐
              │ Merger    │
              └────┬──────┘
                   │
                   ▼
          ┌────────────────┐
          │ LaTeX Writer   │
          └────────┬────────┘
                   │
                   ▼
          ┌────────────────┐
          │ PDF Compiler   │
          └────────┬────────┘
                   │
                   │ Compilation Failed?
                   ├────────────Yes──────────────┐
                   │                              │
                   │                              ▼
                   │                     Fix LaTeX Agent
                   │                      (Max 3x)
                   │                              │
                   └────────────No────────────────┘
                                  │
                                  ▼
                                 END
```

### Research Retry Loop

If the planner does not sufficiently cover all required business sub-topics, the graph automatically routes back to the planner and focuses only on the missing areas.

* Maximum retries: **2**
* Purpose: Improve research completeness.

### LaTeX Self-Healing Loop

If PDF compilation fails due to LaTeX syntax issues, an LLM analyzes the compiler logs, repairs the `.tex` file, and retries compilation automatically.

* Maximum retries: **3**
* Purpose: Improve report generation robustness.

These retry loops are one of the primary reasons for using **LangGraph** instead of a simple sequential pipeline.

---

# Tech Stack

| Category        | Technologies            |
| --------------- | ----------------------- |
| Language        | Python 3.12             |
| Agent Framework | LangGraph               |
| LLM Framework   | LangChain               |
| Models          | Gemini, Groq            |
| Search          | Tavily                  |
| Web Scraping    | Requests, BeautifulSoup |
| Parsing         | Markdownify             |
| PDF Generation  | LaTeX                   |
| Persistence     | SQLite                  |
| Environment     | python-dotenv           |

---

# Project Structure

```text
BusinessResearchAgentLangGraph/
│
├── main.py
├── requirements.txt
├── README.md
├── .env.example
│
├── graph/
│   ├── state.py
│   ├── builder.py
│   └── router.py
│
├── nodes/
│   ├── planner_node.py
│   ├── cleaner_node.py
│   ├── merger_node.py
│   ├── latex_writer_node.py
│   └── latex_compile_node.py
│
├── Tools/
│   ├── search.py
│   ├── scrape.py
│   ├── html_to_md.py
│   ├── md_to_latex.py
│   └── latex_compiler.py
│
├── templates/
│
├── data/
│   ├── outputs/
│   ├── cleaned_outputs/
│   ├── merged_output/
│   └── final_reports/
│
└── checkpoints/
```

---

# Workflow

```text
User Topic
      ↓
Web Search
      ↓
Web Scraping
      ↓
Data Cleaning
      ↓
Report Merging
      ↓
Markdown → LaTeX
      ↓
PDF Generation
      ↓
Final Business Report
```

---

# Why LangGraph?

A traditional script would simply execute:

```python
planner()
cleaner()
merger()
writer()
compiler()
```

and immediately fail whenever:

* Research coverage is incomplete.
* PDF compilation encounters an error.

LangGraph enables:

 Conditional Routing
 Shared State Management
 Retry Mechanisms
 Persistent Checkpointing
 Autonomous Recovery
 Stateful Multi-Agent Workflows

This makes the system significantly more robust and production-oriented.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/Abdullah9712/BusinessResearchAgentLangGraph.git
cd BusinessResearchAgentLangGraph
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment variables:

```bash
cp .env.example .env
```

Add your API keys:

```env
GOOGLE_API_KEY=
GROQ_API_KEY=
TAVILY_API_KEY=
```

---

# LaTeX Requirement

Install one of the following:

### Recommended

* Tectonic

### Alternatives

* MiKTeX
* TeX Live
* MacTeX

Verify installation:

```bash
pdflatex --version
```

or

```bash
tectonic --version
```

---

# Running the Project

```bash
python main.py
```

Example:

```text
Enter Topic:

Poultry Farming Business
```

Generated report:

```text
data/final_reports/business_report.pdf
```

---

# Resumability

The project uses LangGraph checkpointing through SQLite.

If execution stops due to:

* Internet failures
* API quota limits
* LaTeX compilation errors
* Manual interruption

simply rerun the same topic and the pipeline resumes from the last successfully completed node.

---

# Example Output

The generated report may include:

* Executive Summary
* Industry Overview
* Market Size & Growth
* Competitor Analysis
* Revenue Models
* Supply Chain Analysis
* Opportunities & Risks
* Regulations & Compliance
* References

All packaged into a professional PDF report.

---

# Future Improvements

* Streamlit Web Interface
* Parallel Research Agents
* Source Verification Agent
* Citation Generation
* Vector Database Integration
* RAG Support
* Docker Deployment
* Cloud Deployment
* Multi-Language Reports

---

# Learning Outcomes

This project demonstrates knowledge in:

* Agentic AI Systems
* Multi-Agent Architectures
* LangGraph
* Workflow Automation
* State Machines
* LLM Engineering
* Autonomous Agents
* AI Pipeline Design
* Software Engineering Principles

---

# Future Demo Section

```md
## Demo

![Architecture](assets/architecture.png)

![Generated Report](assets/sample_report.png)
```

---

# License

This project is released under the MIT License.

---

# Author

**Muhammad Abdullah**
BS Artificial Intelligence Student
Pak-Austria Fachhochschule Institute of Applied Sciences and Technology

 Email: [abdullah2648.khan@gmail.com](mailto:abdullah2648.khan@gmail.com)

 LinkedIn:
https://www.linkedin.com/in/muhammad-abdullah-963016302

 GitHub:
https://github.com/Abdullah9712
