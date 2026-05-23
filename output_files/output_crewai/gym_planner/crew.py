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
# TODO: fitness_calculator_tools — unknown tool class "fitnesscalculatortools"
#   Description: A tool to calculate Body Mass Index (BMI), Basal Metabolic Rate (BMR), and Total
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# fitness_calculator_tools = SomeCustomTool()



@CrewBase
class MyCrew:
    """MyCrew crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def fitness_expert_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['fitness_expert_agent'],
        )

    @agent
    def nutritionist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['nutritionist_agent'],
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def create_workout_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_workout_task'],
            agent=self.fitness_expert_agent(),
        )

    @task
    def create_meal_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_meal_plan_task'],
            agent=self.nutritionist_agent(),
            context=[self.create_workout_task()],
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
