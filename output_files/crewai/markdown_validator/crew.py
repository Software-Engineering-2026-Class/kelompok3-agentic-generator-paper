"""
Auto-generated CrewAI Crew: MarkDownValidatorCrew

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


# ===========================================================
# Tool Instances
# ===========================================================
# TODO: markdown_validation_tool — unknown tool class "markdownvalidationtool"
#   Description: Tool definition (from src/markdown_validator/tools/markdownTools.py):
- Tool na
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# markdown_validation_tool = SomeCustomTool(tool_registration_name="markdown_validation_tool")



@CrewBase
class MarkDownValidatorCrew:
    """MarkDownValidatorCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def requirements_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['requirements_manager'],
            tools=[markdown_validation_tool],
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def syntax_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['syntax_review_task'],
            agent=self.requirements_manager(),
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the MarkDownValidatorCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
