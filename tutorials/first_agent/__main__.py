"""Print the five runnable lessons without calling a model."""


def main():
    print("Build Your First AI Agent — Python")
    for part, title in enumerate(
        [
            "One checked tool call",
            "The agent loop",
            "Stopping rules",
            "User approval and a local outbox",
            "Python agent + Go MCP",
        ],
        1,
    ):
        print(
            f"{part:02d}. {title}: make run-python SERIES=first_agent PART={part:02d}"
        )
    print("Default: simulated model. Add ARGS='--live' for OpenRouter.")
    print("Part 5 requires: make build-mcp")


if __name__ == "__main__":
    main()
