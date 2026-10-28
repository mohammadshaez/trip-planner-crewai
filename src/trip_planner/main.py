#!/usr/bin/env python
"""Main entry point for the Trip Planner CrewAI project.

Runs the hierarchical TripPlanner crew with configurable inputs.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure 'src' is in Python's module search path when executed directly
project_src = Path(__file__).resolve().parent.parent
if str(project_src) not in sys.path:
    sys.path.insert(0, str(project_src))

# Load environment variables (.env)
load_dotenv()

from trip_planner.crew import TripPlannerCrew


def run():
    """Kickoff the hierarchical Trip Planner Crew.

    Default inputs can be customized here or overridden dynamically.
    """
    inputs = {
        "destination": "Kyoto, Japan",
        "number_of_days": "5",
        "budget_tier": "mid",
        "interests": "food-focused cultural exploration, authentic tea houses, and historic temples",
    }

    print("\n" + "=" * 70)
    print("🌍 KICKING OFF TRIP PLANNER HIERARCHICAL CREW")
    print(f"📍 Destination : {inputs['destination']}")
    print(f"📅 Duration    : {inputs['number_of_days']} days")
    print(f"💰 Budget Tier : {inputs['budget_tier'].capitalize()}")
    print(f"🎯 Interests   : {inputs['interests']}")
    print(f"🤖 Model       : {os.getenv('MODEL', 'gpt-4o-mini')}")
    print(f"🔍 Search Tool : {'Enabled (SerperDevTool)' if os.getenv('SERPER_API_KEY') else 'Offline Mode (LLM Knowledge)'}")
    print("=" * 70 + "\n")

    try:
        crew_instance = TripPlannerCrew().crew()
        result = crew_instance.kickoff(inputs=inputs)

        print("\n" + "=" * 70)
        print("🎉 TRIP PLANNING COMPLETE — FINAL RESULT")
        print("=" * 70 + "\n")
        print(result.raw)

        output_path = Path("output/trip_plan.md")
        if output_path.exists():
            print("\n" + "-" * 70)
            print(f"📁 Full trip dossier saved to: {output_path.resolve()}")
            print("-" * 70)

        return result
    except Exception as e:
        print(f"\n❌ Error during crew execution: {e}", file=sys.stderr)
        raise e


def train():
    """Train the crew for a specified number of iterations."""
    inputs = {
        "destination": "Kyoto, Japan",
        "number_of_days": "5",
        "budget_tier": "mid",
        "interests": "food-focused cultural exploration and historic temples",
    }
    try:
        TripPlannerCrew().crew().train(
            n_iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 2,
            filename=sys.argv[2] if len(sys.argv) > 2 else "trained_agents.pkl",
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        TripPlannerCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and returns the results."""
    inputs = {
        "destination": "Italy",
        "number_of_days": "5",
        "budget_tier": "mid",
        "interests": "food-focused cultural exploration and historic temples",
    }
    try:
        eval_model = sys.argv[2] if len(sys.argv) > 2 else os.getenv("MODEL", "gpt-4o-mini")
        TripPlannerCrew().crew().test(
            n_iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 2,
            eval_llm=eval_model,
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()
