"""
Auto-generated CrewAI Crew: CopyCrew

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from langchain.llms import Ollama

# ===========================================================
# Tool Instances
# ===========================================================
# TODO: tool_browser_tools_scrape_and_summarize — unknown tool class "BrowserToolsscrapeandsummarizewebsite"
#   Description: Semantic purpose: Scrape a website and produce a long summary of its content or 
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# tool_browser_tools_scrape_and_summarize = SomeCustomTool(BROWSERLESS_API_KEY="REQUIRES_VALID_KEY")
# TODO: tool_search_tools_search_internet — unknown tool class "SearchToolssearchinternet"
#   Description: Semantic purpose: Search the Internet (generic web search) and return top organi
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# tool_search_tools_search_internet = SomeCustomTool(SERPER_API_KEY="REQUIRES_VALID_KEY")
# TODO: tool_search_tools_search_instagram — unknown tool class "SearchToolssearchinstagram"
#   Description: Semantic purpose: Search Instagram via site-limited search (site:instagram.com) 
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# tool_search_tools_search_instagram = SomeCustomTool(SERPER_API_KEY="REQUIRES_VALID_KEY")

# ===========================================================
# Custom LLM
# ===========================================================
product_competitor_agent_llm = Ollama(model="local")
strategy_planner_agent_llm = Ollama(model="local")
creative_content_creator_agent_llm = Ollama(model="local")
senior_photographer_agent_llm = Ollama(model="local")
chief_creative_director_agent_llm = Ollama(model="local")


@CrewBase
class CopyCrew:
    """CopyCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def product_competitor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['product_competitor_agent'],
            llm=product_competitor_agent_llm,
            verbose=True,
        )

    @agent
    def strategy_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['strategy_planner_agent'],
            llm=strategy_planner_agent_llm,
            verbose=True,
        )

    @agent
    def creative_content_creator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['creative_content_creator_agent'],
            llm=creative_content_creator_agent_llm,
            verbose=True,
        )

    @agent
    def senior_photographer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_photographer_agent'],
            llm=senior_photographer_agent_llm,
            verbose=True,
        )

    @agent
    def chief_creative_director_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['chief_creative_director_agent'],
            llm=chief_creative_director_agent_llm,
            verbose=True,
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def task_product_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['task_product_analysis'],
            agent=self.product_competitor_agent(),
        )

    @task
    def task_take_photograph(self) -> Task:
        return Task(
            config=self.tasks_config['task_take_photograph'],
            agent=self.senior_photographer_agent(),
            context=[self.task_instagram_ad_copy(), self.task_product_analysis()],
        )

    @task
    def task_competitor_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['task_competitor_analysis'],
            agent=self.product_competitor_agent(),
        )

    @task
    def task_review_photo(self) -> Task:
        return Task(
            config=self.tasks_config['task_review_photo'],
            agent=self.chief_creative_director_agent(),
            context=[self.task_take_photograph(), self.task_product_analysis()],
        )

    @task
    def task_campaign_development(self) -> Task:
        return Task(
            config=self.tasks_config['task_campaign_development'],
            agent=self.strategy_planner_agent(),
            context=[self.task_product_analysis(), self.task_competitor_analysis()],
        )

    @task
    def task_instagram_ad_copy(self) -> Task:
        return Task(
            config=self.tasks_config['task_instagram_ad_copy'],
            agent=self.creative_content_creator_agent(),
            context=[self.task_campaign_development()],
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the CopyCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
