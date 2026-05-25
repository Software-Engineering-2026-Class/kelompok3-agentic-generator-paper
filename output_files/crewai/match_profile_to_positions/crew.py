"""
Auto-generated CrewAI Crew: MyCrew

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from crewai_tools import FileReadTool, CSVSearchTool

# ===========================================================
# Tool Instances
# ===========================================================
file_read_tool = FileReadTool(description="Reads and returns file contents given a path. Used to access CV and any file-based resources.")
csv_search_tool = CSVSearchTool(description="Searches CSV files and extracts rows matching criteria. Used to parse the jobs CSV.")
# TODO: my_custom_tool — unknown tool class "mycustomtool"
#   Description: Custom tool implemented at src/match_to_proposal/tools/job_db_connect.py. Placeh
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# my_custom_tool = SomeCustomTool(name="Name of my tool", name="Clear description for what this tool is useful for, your agent will need this information to use it.", description="Name of my tool", description="Clear description for what this tool is useful for, your agent will need this information to use it.")



@CrewBase
class MyCrew:
    """MyCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def cv_reader(self) -> Agent:
        return Agent(
            config=self.agents_config['cv_reader'],
            tools=[file_read_tool],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def matcher(self) -> Agent:
        return Agent(
            config=self.agents_config['matcher'],
            tools=[file_read_tool, csv_search_tool],
            allow_delegation=False,
            verbose=True,
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def read_cv_task(self) -> Task:
        return Task(
            config=self.tasks_config['read_cv_task'],
            agent=self.cv_reader(),
        )

    @task
    def match_cv_task(self) -> Task:
        return Task(
            config=self.tasks_config['match_cv_task'],
            agent=self.matcher(),
            context=[self.read_cv_task()],
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
