"""
Auto-generated CrewAI Crew: MeetingPreparationCrew

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


# ===========================================================
# Tool Instances
# ===========================================================
# TODO: exa_search_tool — unknown tool class "ExaSearchTool"
#   Description: Tool wrapping Exa (exa_py) search capabilities used by agents.
Provides three m
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# exa_search_tool = SomeCustomTool(EXA_API_KEY="Your Key (from .env.example)")



@CrewBase
class MeetingPreparationCrew:
    """MeetingPreparationCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def researcher_agent_1(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher_agent_1'],
            tools=[exa_search_tool],
        )

    @agent
    def industry_analyst_agent_1(self) -> Agent:
        return Agent(
            config=self.agents_config['industry_analyst_agent_1'],
            tools=[exa_search_tool],
        )

    @agent
    def meeting_strategy_agent_1(self) -> Agent:
        return Agent(
            config=self.agents_config['meeting_strategy_agent_1'],
            tools=[exa_search_tool],
        )

    @agent
    def briefing_coordinator_agent_1(self) -> Agent:
        return Agent(
            config=self.agents_config['briefing_coordinator_agent_1'],
            tools=[exa_search_tool],
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher_agent_1(),
        )

    @task
    def industry_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['industry_analysis_task'],
            agent=self.industry_analyst_agent_1(),
        )

    @task
    def meeting_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['meeting_strategy_task'],
            agent=self.meeting_strategy_agent_1(),
        )

    @task
    def summary_and_briefing_task(self) -> Task:
        return Task(
            config=self.tasks_config['summary_and_briefing_task'],
            agent=self.briefing_coordinator_agent_1(),
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the MeetingPreparationCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
