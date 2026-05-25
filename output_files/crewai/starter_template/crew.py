"""
Auto-generated CrewAI Crew: MyCrew

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


# ===========================================================
# Tool Instances
# ===========================================================
# TODO: duck_duck_go_tool — unknown tool class "duckduckgotool"
#   Description: An instance of DuckDuckGoSearchRun created in main.py and intended for web searc
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# duck_duck_go_tool = SomeCustomTool(tool_class="DuckDuckGoSearchRun (langchain.tools)")



@CrewBase
class MyCrew:
    """MyCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def agent_1_name(self) -> Agent:
        return Agent(
            config=self.agents_config['agent_1_name'],
            tools=[duck_duck_go_tool],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def agent_2_name(self) -> Agent:
        return Agent(
            config=self.agents_config['agent_2_name'],
            tools=[duck_duck_go_tool],
            allow_delegation=False,
            verbose=True,
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def task_1(self) -> Task:
        return Task(
            config=self.tasks_config['task_1'],
            agent=self.agent_1_name(),
        )

    @task
    def task_2(self) -> Task:
        return Task(
            config=self.tasks_config['task_2'],
            agent=self.agent_2_name(),
            context=[self.task_1()],
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the MyCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
