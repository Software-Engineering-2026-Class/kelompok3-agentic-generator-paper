import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREAI_TTL_DIR = os.path.join(PROJECT_ROOT, "generated_kg", "CrewAI")
LANGGRAPH_TTL_DIR = os.path.join(PROJECT_ROOT, "generated_kg", "LangGraph")

EXT_PREFIX = '@prefix agento-ext: <http://www.w3id.org/agentic-ai/ext#> .'

CREW_INPUTS = {
    "game-builder-crew_instances": [
        ("game", "A Snake game where the player controls a snake that moves continuously, and the player can change its direction using input keys. The snake grows longer each time it eats food, which appears randomly on the screen. The game ends if the snake collides with itself or the walls. The player's score increases with each food item eaten. The game should include a simple scoring system, a start screen, and a game-over screen displaying the final score.", True),
    ],
    "industry-agents_instances": [
        ("weaviate_feature", "MUVERA", True),
    ],
    "instagram_post_instances": [
        ("product_website", "", False),
        ("product_details", "", False),
    ],
    "job-posting_instances": [
        ("company_domain", "careers.wbd.com", True),
        ("company_description", "Warner Bros. Discovery is a premier global media and entertainment company, offering audiences the world's most differentiated and complete portfolio of content, brands and franchises across television, film, sports, news, streaming and gaming. We're home to the world's best storytellers, creating world-class products for consumers", True),
        ("hiring_needs", "Production Assistant, for a TV production set in Los Angeles in June 2025", True),
        ("specific_benefits", "Weekly Pay, Employee Meals, healthcare", True),
    ],
    "landing_page_generator_instances": [
        ("idea", "", False),
    ],
    "markdown_validator_instances": [
        ("filename", "", False),
    ],
    "marketing_strategy_instances": [
        ("customer_domain", "crewai.com", True),
        ("project_description", "CrewAI, a leading provider of multi-agent systems, aims to revolutionize marketing automation for its enterprise clients. This project involves developing an innovative marketing strategy to showcase CrewAI's advanced AI-driven solutions, emphasizing ease of use, scalability, and integration capabilities. The campaign will target tech-savvy decision-makers in medium to large enterprises, highlighting success stories and the transformative potential of CrewAI's platform.", True),
    ],
    "match_profile_to_positions_instances": [
        ("path_to_cv", "./src/match_to_proposal/data/cv.md", True),
        ("path_to_jobs_csv", "./src/match_to_proposal/data/jobs.csv", True),
    ],
    "meta_quest_knowledge_instances": [
        ("question", "How often should I take breaks?", True),
    ],
    "prep-for-a-meeting_instances": [
        ("participants", "", False),
        ("context", "", False),
        ("objective", "", False),
    ],
    "recruitment_instances": [
        ("job_requirements", "Ruby on Rails and React Engineer - We are seeking a skilled Ruby on Rails and React engineer to join our team. The ideal candidate will have experience in both backend and frontend development, with a passion for building high-quality web applications.", True),
    ],
    "screenplay_writer_instances": [],
    "starter_template_instances": [
        ("var1", "", False),
        ("var2", "", False),
    ],
    "stock_analysis_instances": [
        ("company_stock", "AMZN", True),
    ],
    "surprise_trip_instances": [
        ("origin", "São Paulo, GRU", True),
        ("destination", "New York, JFK", True),
        ("age", "31", True),
        ("hotel_location", "Brooklyn", True),
        ("flight_information", "GOL 1234, leaving at June 30th, 2024, 10:00", True),
        ("trip_duration", "14 days", True),
    ],
    "trip_planner_instances": [
        ("origin", "", False),
        ("cities", "", False),
        ("range", "", False),
        ("interests", "", False),
    ],
}

LANGGRAPH_INPUTS = {
    "chat-agent_instances": [],
    "email-agent_instances": [
        ("recipient", "user@example.com", True),
        ("subject", "Quick question about the project", True),
        ("body", "Hi, I wanted to follow up on our last conversation about the project timeline. Can you send me an update when you have a moment? Thanks!", True),
    ],
    "open-code_instances": [
        ("request", "Write a Python function that reads a CSV file and returns a list of dictionaries, one per row. Include error handling for missing files and malformed rows.", True),
    ],
    "pizza-orderer_instances": [
        ("pizza_type", "Margherita", True),
        ("size", "large", True),
        ("toppings", "extra cheese, mushrooms", True),
        ("delivery_address", "123 Main St, Springfield", True),
    ],
    "stockbroker_instances": [
        ("stock_ticker", "AAPL", True),
        ("analysis_type", "short-term outlook", True),
    ],
    "supervisor_instances": [
        ("task_description", "Investigate the Q3 sales drop and produce a report with findings and recommendations.", True),
    ],
    "trip-planner_instances": [
        ("location", "Bali, Indonesia", True),
        ("startDate", "2026-08-15", True),
        ("endDate", "2026-08-22", True),
        ("numberOfGuests", "2", True),
        ("interests", "beaches, temples, local food", True),
    ],
    "utils_instances": [],
    "writer-agent_instances": [
        ("topic", "The impact of remote work on team collaboration", True),
        ("tone", "professional but conversational", True),
        ("length", "500 words", True),
    ],
}


def _escape_ttl(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def build_bundle_block(stem: str, inputs: list) -> str:
    if not inputs:
        return ""

    lines = [
        "",
        "################################################################################",
        "# KickoffInputBundle (agento-ext) - Uniform runtime inputs for pipeline extraction",
        "################################################################################",
        "",
    ]

    for key, value, is_default in inputs:
        node_name = f":KickoffInput_{key}"
        escaped_val = _escape_ttl(value)

        lines.append(f'{node_name} a agento-ext:KickoffInputBundle ;')
        lines.append(f'    agento-ext:inputKey "{key}" ;')
        if is_default and value:
            lines.append(f'    agento-ext:inputValue "{escaped_val}" ;')
        else:
            lines.append(f'    agento-ext:inputValue "" ;')
        lines.append(f'    agento-ext:isDefaultValue {"true" if (is_default and value) else "false"} .')
        lines.append("")

    return "\n".join(lines)


def process_file(filepath: str, stem: str, inputs: list) -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "agento-ext:" in content:
        print(f"  [SKIP] {stem} - already has agento-ext triples")
        return

    prefix_lines = []
    other_lines = []
    in_prefix_block = True
    for line in content.split("\n"):
        if in_prefix_block and (line.startswith("@prefix") or line.startswith("@base")):
            prefix_lines.append(line)
        elif in_prefix_block and line.strip() == "" and prefix_lines:
            prefix_lines.append(line)
        else:
            if in_prefix_block and prefix_lines:
                in_prefix_block = False
            other_lines.append(line)

    prefix_lines.insert(-1, EXT_PREFIX)

    bundle_block = build_bundle_block(stem, inputs)
    new_content = "\n".join(prefix_lines) + "\n" + "\n".join(other_lines)
    new_content = new_content.rstrip() + "\n" + bundle_block

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    n_inputs = len(inputs)
    has_defaults = sum(1 for _, v, d in inputs if d and v)
    print(f"  [OK] {stem} - {n_inputs} inputs ({has_defaults} with defaults)")


def process_directory(ttl_dir: str, inputs_dict: dict, label: str) -> None:
    print(f"\n[{label}] processing {ttl_dir}")
    if not os.path.isdir(ttl_dir):
        print(f"  [WARN] directory not found, skipping")
        return
    for stem, inputs in inputs_dict.items():
        filepath = os.path.join(ttl_dir, f"{stem}.ttl")
        if not os.path.exists(filepath):
            print(f"  [WARN] {stem}.ttl not found, skipping")
            continue
        process_file(filepath, stem, inputs)


def main():
    print("Adding agento-ext:KickoffInputBundle to TTL files...")
    process_directory(CREAI_TTL_DIR, CREW_INPUTS, "CrewAI")
    process_directory(LANGGRAPH_TTL_DIR, LANGGRAPH_INPUTS, "LangGraph")
    print("\nDone! All TTL files updated.")


if __name__ == "__main__":
    main()
