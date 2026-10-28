"""Trip Planner Crew Definition.

This module implements a collaborative, multi-agent trip planning system
governed by a hierarchical process (Process.hierarchical). A central Manager LLM
coordinates three specialist agents: Destination Researcher, Itinerary Planner,
and Budget Estimator.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

# Load environment variables
load_dotenv()


def get_llm() -> LLM:
    """Configures and returns the LLM instance based on environment variables.

    Supported configurations:
    1. Default (OpenAI):
       MODEL="gpt-4o-mini" (or "gpt-4o")
       OPENAI_API_KEY="sk-..."

    2. Groq (Fast open models via OpenAI-compatible API):
       MODEL="groq/llama-3.3-70b-versatile"
       GROQ_API_KEY="gsk_..."

    3. Ollama (100% Local & Free):
       MODEL="ollama/llama3.1"
       OLLAMA_BASE_URL="http://localhost:11434"

    4. Google Gemini:
       MODEL="gemini/gemini-2.0-flash"
       GEMINI_API_KEY="..."
    """
    model = os.getenv("MODEL", "gpt-4o-mini")

    # 1. Local Ollama integration
    if model.startswith("ollama/"):
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return LLM(model=model, base_url=base_url)

    # 2. Groq via OpenAI-compatible endpoint
    if model.startswith("groq/"):
        raw_model = model.replace("groq/", "")
        return LLM(
            model=f"openai/{raw_model}",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )

    # 3. Standard native provider (OpenAI, Gemini, Anthropic, etc.)
    return LLM(model=model)


def get_research_tools() -> list:
    """Guarded tool initializer.

    Returns SerperDevTool if SERPER_API_KEY is configured in the environment.
    If no key is present, returns an empty list so the crew runs reliably
    using the LLM's internal knowledge base without crashing.
    """
    serper_api_key = os.getenv("SERPER_API_KEY")
    if serper_api_key and serper_api_key.strip() and not serper_api_key.startswith("your_"):
        try:
            return [SerperDevTool()]
        except Exception as e:
            print(f"[Warning] Failed to initialize SerperDevTool ({e}). Proceeding without web search.")
            return []
    return []


@CrewBase
class TripPlannerCrew:
    """TripPlanner hierarchical crew definition."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # =========================================================================
    # WORKER AGENTS
    # =========================================================================

    @agent
    def destination_researcher(self) -> Agent:
        """Agent 1: Destination Research Specialist.

        Equipped with optional web search tools (SerperDevTool) when an API key
        is present to verify current attraction schedules, seasonal events, and
        neighborhood dining spots.
        """
        return Agent(
            config=self.agents_config["destination_researcher"],
            tools=get_research_tools(),
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def itinerary_planner(self) -> Agent:
        """Agent 2: Master Travel Itinerary Architect.

        Synthesizes research into practical, geographically grouped daily schedules
        (Morning/Afternoon/Evening) with realistic transit buffer times.
        """
        return Agent(
            config=self.agents_config["itinerary_planner"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def budget_estimator(self) -> Agent:
        """Agent 3: Travel Financial Analyst & Cost Estimator.

        Produces an itemized financial cost breakdown (flights, lodging, food,
        activities, transport) formatted in a clear Markdown table.
        """
        return Agent(
            config=self.agents_config["budget_estimator"],
            llm=get_llm(),
            verbose=True,
        )

    # =========================================================================
    # TASKS
    # =========================================================================

    @task
    def research_destination_task(self) -> Task:
        """Task 1: Gathers foundational destination knowledge.

        Investigates attractions, neighborhoods, local food, weather, and practical tips.
        """
        return Task(
            config=self.tasks_config["research_destination_task"],
        )

    @task
    def plan_itinerary_task(self) -> Task:
        """Task 2: Designs the day-by-day travel itinerary.

        Explicitly depends on the output of research_destination_task via context.
        """
        return Task(
            config=self.tasks_config["plan_itinerary_task"],
            context=[self.research_destination_task()],
        )

    @task
    def estimate_budget_task(self) -> Task:
        """Task 3: Estimates trip expenses and compiles final trip dossier.

        Depends on both destination research and itinerary tasks to compute realistic
        costs for accommodations, dining, transit, and entry fees. Saves final dossier
        to output/trip_plan.md.
        """
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        return Task(
            config=self.tasks_config["estimate_budget_task"],
            context=[self.research_destination_task(), self.plan_itinerary_task()],
            output_file="output/trip_plan.md",
        )

    # =========================================================================
    # HIERARCHICAL CREW ORCHESTRATION
    # =========================================================================

    @crew
    def crew(self) -> Crew:
        """Creates and configures the hierarchical Crew.

        Key Architectural Highlights:
        - process=Process.hierarchical: Enables manager-driven delegation.
        - manager_llm=get_llm(): Supplies the intelligence engine for the
          built-in Manager Agent ('Crew Manager'). The manager analyzes each
          task, delegates questions/sub-tasks to the three specialist agents,
          validates their outputs, and assembles the final result.
        - agents: Automatically collected by the @agent decorator.
        - tasks: Automatically collected by the @task decorator.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm=get_llm(),
            verbose=True,
        )
