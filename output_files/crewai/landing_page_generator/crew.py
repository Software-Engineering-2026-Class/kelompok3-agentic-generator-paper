"""
Auto-generated CrewAI Crew: ExpandIdeaCrewteam

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


# ===========================================================
# Tool Instances
# ===========================================================
# TODO: search_internet_tool — unknown tool class "SearchtheinternetSearchToolssearchinternet"
#   Description: Performs internet search using an external search API (serper.dev). Requires SER
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# search_internet_tool = SomeCustomTool()
# TODO: scrape_website_tool — unknown tool class "ScrapewebsitecontentBrowserToolsscrapeandsummarizewebsite"
#   Description: Scrapes website HTML via browserless API and summarizes content using an interna
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# scrape_website_tool = SomeCustomTool()
# TODO: write_file_tool — unknown tool class "WritefiletoworkdirFileToolswritefile"
#   Description: Writes files into ./workdir with path sanitization and allowed extensions.
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# write_file_tool = SomeCustomTool()
# TODO: learn_templates_tool — unknown tool class "LearnlandingpageoptionsTemplateToolslearnlandingpageoptions"
#   Description: Reads config/templates.json to list available templates.
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# learn_templates_tool = SomeCustomTool()
# TODO: copy_template_tool — unknown tool class "CopylandingpagetemplatetoprojectfolderTemplateToolscopylandingpagetemplatetoprojectfolder"
#   Description: Copies a template folder from ./templates to ./workdir with safety checks.
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# copy_template_tool = SomeCustomTool()
# TODO: read_file_tool — unknown tool class "Readfilefilemanagementtoolkitreadfile"
#   Description: Read file contents from workdir (used by agent toolkits).
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# read_file_tool = SomeCustomTool()
# TODO: list_directory_tool — unknown tool class "Listdirectoryfilemanagementtoolkitlistdirectory"
#   Description: List directories in workdir (used by agent toolkits).
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# list_directory_tool = SomeCustomTool()
# TODO: file_management_toolkit — unknown tool class "Filemanagementtoolkitcontainerprovidesreadfilelistdirectorytools"
#   Description: In the code this is an instantiation of FileManagementToolkit(root_dir='workdir'
#   Implement as a custom BaseTool or replace with a crewai_tools equivalent.
# file_management_toolkit = SomeCustomTool()



@CrewBase
class ExpandIdeaCrewteam:
    """ExpandIdeaCrewteam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ──────────────────────────────────────────

    @agent
    def senior_idea_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_idea_analyst'],
            tools=[search_internet_tool, scrape_website_tool],
        )

    @agent
    def senior_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_strategist'],
            tools=[search_internet_tool, scrape_website_tool],
        )

    @agent
    def senior_react_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_react_engineer'],
            tools=[search_internet_tool, scrape_website_tool, write_file_tool, learn_templates_tool, copy_template_tool, read_file_tool, list_directory_tool],
        )

    @agent
    def senior_content_editor(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_content_editor'],
            tools=[write_file_tool, read_file_tool, list_directory_tool],
        )

    # ── Tasks ───────────────────────────────────────────

    @task
    def expand_idea_task(self) -> Task:
        return Task(
            config=self.tasks_config['expand_idea_task'],
            agent=self.senior_idea_analyst(),
        )

    @task
    def choose_template_task(self) -> Task:
        return Task(
            config=self.tasks_config['choose_template_task'],
            agent=self.senior_react_engineer(),
            context=[self.refine_idea_task()],
        )

    @task
    def component_content_task(self) -> Task:
        return Task(
            config=self.tasks_config['component_content_task'],
            agent=self.senior_content_editor(),
            context=[self.refine_idea_task(), self.update_page_task()],
        )

    @task
    def refine_idea_task(self) -> Task:
        return Task(
            config=self.tasks_config['refine_idea_task'],
            agent=self.senior_strategist(),
            context=[self.expand_idea_task()],
        )

    @task
    def update_page_task(self) -> Task:
        return Task(
            config=self.tasks_config['update_page_task'],
            agent=self.senior_react_engineer(),
            context=[self.choose_template_task()],
        )

    @task
    def update_component_task(self) -> Task:
        return Task(
            config=self.tasks_config['update_component_task'],
            agent=self.senior_content_editor(),
            context=[self.component_content_task(), self.update_page_task()],
        )

    @task
    def qa_component_task(self) -> Task:
        return Task(
            config=self.tasks_config['qa_component_task'],
            agent=self.senior_content_editor(),
            context=[self.update_component_task()],
        )

    # ── Crew ────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the ExpandIdeaCrewteam"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
