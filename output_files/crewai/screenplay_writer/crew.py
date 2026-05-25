"""
Auto-generated CrewAI Crew: AICrewforscreenwriting

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task




@CrewBase
class AICrewforscreenwriting:
    """AICrewforscreenwriting crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def spamfilter(self) -> Agent:
        return Agent(
            config=self.agents_config['spamfilter'],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def scriptwriter(self) -> Agent:
        return Agent(
            config=self.agents_config['scriptwriter'],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def formatter(self) -> Agent:
        return Agent(
            config=self.agents_config['formatter'],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def scorer(self) -> Agent:
        return Agent(
            config=self.agents_config['scorer'],
            allow_delegation=False,
            verbose=True,
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def task1_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['task1_analysis'],
            agent=self.analyst(),
        )

    @task
    def task2_scriptwriting(self) -> Task:
        return Task(
            config=self.tasks_config['task2_scriptwriting'],
            agent=self.scriptwriter(),
            context=[self.task1_analysis()],
        )

    @task
    def task3_formatting(self) -> Task:
        return Task(
            config=self.tasks_config['task3_formatting'],
            agent=self.formatter(),
            context=[self.task2_scriptwriting()],
        )

    @task
    def task0_spam_check(self) -> Task:
        return Task(
            config=self.tasks_config['task0_spam_check'],
            agent=self.spamfilter(),
        )

    @task
    def task4_scoring(self) -> Task:
        return Task(
            config=self.tasks_config['task4_scoring'],
            agent=self.scorer(),
            context=[self.task3_formatting()],
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the AICrewforscreenwriting"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
