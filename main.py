from graph.builder import build_graph

def main():
    topic = input("Enter business idea: ")
    graph = build_graph()

    # thread_id ties this run to a checkpoint row, so if it crashes mid-pipeline
    # (e.g. LaTeX compile fails 3x, or you Ctrl+C during scraping), re-running
    # main.py with the SAME topic resumes instead of starting from scratch.
    config = {"configurable": {"thread_id": topic.strip().lower().replace(" ", "_")}}

    print("=" * 60)
    print(f"Starting pipeline for: {topic}")
    print("=" * 60)

    final_state = graph.invoke({"topic": topic}, config=config)

    print("=" * 60)
    if final_state.get("pdf_path"):
        print(f"SUCCESS. Final PDF: {final_state['pdf_path']}")
    else:
        print("Pipeline finished WITHOUT a compiled PDF.")
        print(f"LaTeX source (for manual debugging): {final_state.get('latex_path')}")
        print(f"Last compiler error:\n{final_state.get('compile_error')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
