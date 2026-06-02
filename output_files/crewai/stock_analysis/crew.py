"""
Auto-generated CrewAI Crew: StockAnalysisCrew

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from crewai_tools import ScrapeWebsiteTool, WebsiteSearchTool, TXTSearchTool
from langchain.llms import Ollama

# ===========================================================
# Tool Instances
# ===========================================================
# TODO: tool_calculator — unknown tool class "CalculatorTool"
#   Description: Calculator tool (from src/stock_analysis/tools/calculator_tool.py).
    Purpose:
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# tool_calculator = SomeCustomTool()
tool_scrape_website = ScrapeWebsiteTool()
tool_website_search = WebsiteSearchTool()
tool_txt_search = TXTSearchTool()
# TODO: sec10_k_tool_generic — unknown tool class "SEC10KToolgeneric"
#   Description: A RAG-style tool for semantic search in 10-K filings (class src/stock_analysis/t
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# sec10_k_tool_generic = SomeCustomTool()
# TODO: sec10_k_tool_amzn — unknown tool class "SEC10KToolAMZN"
#   Description: Instance of SEC10KTool initialized with stock_name='AMZN'. On init it attempted 
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# sec10_k_tool_amzn = SomeCustomTool(stock_name="AMZN")
# TODO: sec10_q_tool_generic — unknown tool class "SEC10QToolgeneric"
#   Description: A RAG-style tool for semantic search in 10-Q filings (class src/stock_analysis/t
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# sec10_q_tool_generic = SomeCustomTool()
# TODO: sec10_q_tool_amzn — unknown tool class "SEC10QToolAMZN"
#   Description: Instance of SEC10QTool initialized with stock_name='AMZN'. On init it attempted 
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# sec10_q_tool_amzn = SomeCustomTool(stock_name="AMZN")

# ===========================================================
# Custom LLM
# ===========================================================
financial_agent_llm = Ollama(model="llama3.1")
financial_analyst_agent_llm = Ollama(model="llama3.1")
research_analyst_agent_llm = Ollama(model="llama3.1")
investment_advisor_agent_llm = Ollama(model="llama3.1")


@CrewBase
class StockAnalysisCrew:
    """StockAnalysisCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def financial_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_agent'],
            tools=[tool_calculator, tool_scrape_website, tool_website_search, sec10_k_tool_amzn, sec10_q_tool_amzn],
            llm=financial_agent_llm,
        )

    @agent
    def financial_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst_agent'],
            tools=[tool_calculator, tool_scrape_website, tool_website_search, sec10_k_tool_generic, sec10_q_tool_generic],
            llm=financial_analyst_agent_llm,
        )

    @agent
    def research_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_analyst_agent'],
            tools=[tool_scrape_website, sec10_k_tool_amzn, sec10_q_tool_amzn],
            llm=research_analyst_agent_llm,
        )

    @agent
    def investment_advisor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['investment_advisor_agent'],
            tools=[tool_calculator, tool_scrape_website, tool_website_search],
            llm=investment_advisor_agent_llm,
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def research(self) -> Task:
        return Task(
            config=self.tasks_config['research'],
            agent=self.research_analyst_agent(),
        )

    @task
    def filings_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['filings_analysis'],
            agent=self.financial_analyst_agent(),
        )

    @task
    def financial_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['financial_analysis'],
            agent=self.financial_analyst_agent(),
        )

    @task
    def recommend(self) -> Task:
        return Task(
            config=self.tasks_config['recommend'],
            agent=self.investment_advisor_agent(),
            context=[self.financial_analysis(), self.research(), self.filings_analysis()],
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the StockAnalysisCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
