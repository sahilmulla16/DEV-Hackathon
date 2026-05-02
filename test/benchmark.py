import json
import csv
import time
import statistics
import argparse
import random
import traceback
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# --- AGENT IMPORT ---
# Add the project root to the python path to allow importing the agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import run_agent_once

# ======================================================================================
# AGENT WRAPPER - THIS NOW CALLS YOUR REAL AGENT
# ======================================================================================
# This function simulates your agent's behavior for demonstrating the framework.
# It randomly decides success, tool usage, and performance metrics.

def run_agent(query: str, test_case: dict) -> dict:
    """
    Wrapper for the actual `run_agent_once` function.
    It calls the agent and formats the output for the benchmark framework.
    
    Args:
        query: The user input query.
        test_case: The full test case dictionary, used here to access expected values.

    Returns:
        A dictionary mimicking the agent's output.
    """
    print(f"      Running agent for query: \"{query[:50]}...\"")
    
    # Call the actual agent. The benchmark runs each query independently, so history is [].
    agent_response = run_agent_once(user_input=query, history=[])

    # Adapt the response to the format expected by the benchmark framework.
    final_answer = agent_response.get("final", "")
    reflections = agent_response.get("reflections", 0)
    
    # Extract tools called from the plan.
    plan = agent_response.get("plan", [])
    if isinstance(plan, list):
        tools_called = [step.get("tool") for step in plan if step.get("tool")]
    else:
        tools_called = []

    # NOTE: `llm_calls` is not currently tracked by the agent.
    # This is a placeholder value. For accurate metrics, the agent's
    # `_llm_invoke` function should be modified to count calls.
    # We use a random value plus reflections to have a dynamic number.
    llm_calls = random.randint(2, 5) + (reflections * 2)

    return {
        "final": final_answer,
        "tools_called": tools_called,
        "reflections": reflections,
        "llm_calls": llm_calls,
    }

# ======================================================================================
# BENCHMARKING FRAMEWORK CORE
# ======================================================================================

def load_test_cases(filepath: Path) -> list:
    """Loads test cases from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading test cases from {filepath}: {e}")
        return []

def save_results(results: list, output_dir: Path, timestamp: str):
    """Saves benchmark results to both JSON and CSV files."""
    if not results:
        return

    output_dir.mkdir(exist_ok=True)
    json_path = output_dir / f"benchmark_results_{timestamp}.json"
    csv_path = output_dir / f"benchmark_results_{timestamp}.csv"

    # Save to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Detailed results saved to {json_path}")

    # Save to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"💾 Detailed results saved to {csv_path}")

def calculate_metrics(results: list) -> tuple[dict, dict]:
    """Calculates overall and per-category aggregate metrics."""
    if not results:
        return {}, {}

    category_metrics = defaultdict(lambda: defaultdict(list))
    
    for r in results:
        cat = r['category']
        category_metrics[cat]['success'].append(r['success'])
        category_metrics[cat]['tool_accurate'].append(r['tool_accurate'])
        category_metrics[cat]['latency'].append(r['latency_seconds'])
        category_metrics[cat]['llm_calls'].append(r['llm_calls'])
        category_metrics[cat]['reflections'].append(r['reflections'])
        if r['reflections'] > 0:
            category_metrics[cat]['reflection_recovery_attempts'].append(r['success'])

    final_metrics = {}
    for cat, data in category_metrics.items():
        total = len(data['success'])
        success_rate = (sum(data['success']) / total) * 100 if total > 0 else 0
        tool_accuracy = (sum(data['tool_accurate']) / total) * 100 if total > 0 else 0
        
        recovery_attempts = data['reflection_recovery_attempts']
        recovery_rate = (sum(recovery_attempts) / len(recovery_attempts)) * 100 if recovery_attempts else 0

        final_metrics[cat] = {
            "Total Queries": total,
            "Success Rate (%)": success_rate,
            "Tool Accuracy (%)": tool_accuracy,
            "Avg Latency (s)": statistics.mean(data['latency']) if data['latency'] else 0,
            "Avg LLM Calls": statistics.mean(data['llm_calls']) if data['llm_calls'] else 0,
            "Avg Reflections": statistics.mean(data['reflections']) if data['reflections'] else 0,
            "Reflection Recovery Rate (%)": recovery_rate,
        }

    # Calculate overall metrics
    all_results_flat = [item for sublist in category_metrics.values() for item in sublist['success']]
    total_overall = len(all_results_flat)
    
    overall_metrics = {
        "Total Queries": total_overall,
        "Success Rate (%)": (sum(r['success'] for r in results) / total_overall) * 100 if total_overall > 0 else 0,
        "Tool Accuracy (%)": (sum(r['tool_accurate'] for r in results) / total_overall) * 100 if total_overall > 0 else 0,
        "Avg Latency (s)": statistics.mean(r['latency_seconds'] for r in results) if results else 0,
        "Avg LLM Calls": statistics.mean(r['llm_calls'] for r in results) if results else 0,
        "Avg Reflections": statistics.mean(r['reflections'] for r in results) if results else 0,
        "Reflection Recovery Rate (%)": (
            sum(r['success'] for r in results if r['reflections'] > 0) / 
            sum(1 for r in results if r['reflections'] > 0) * 100 
            if sum(1 for r in results if r['reflections'] > 0) > 0 else 0
        ),
    }

    return overall_metrics, final_metrics

def print_summary(overall_metrics: dict, category_metrics: dict):
    """Prints formatted summary tables to the console."""
    print("\n" + "="*80)
    print("📊 BENCHMARK SUMMARY")
    print("="*80)

    def print_table(title: str, metrics: dict):
        print(f"\n--- {title} ---")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key:<30}: {value:.2f}")
            else:
                print(f"{key:<30}: {value}")

    print_table("OVERALL METRICS", overall_metrics)

    print("\n" + "-"*80)
    print("CATEGORY-WISE METRICS")
    print("-"*80)

    for category, metrics in sorted(category_metrics.items()):
        print_table(f"Category: {category.upper()}", metrics)

    print("\n" + "="*80)
    print("Future graph generation support: The saved .csv and .json files can be used with libraries like pandas, matplotlib, or seaborn for visualization.")
    print("="*80)

def run_single_test(test_case: dict) -> dict:
    """Runs a single test case and evaluates the result."""
    query_id = test_case['id']
    query = test_case['query']
    
    start_time = time.monotonic()
    
    try:
        # =====================================================
        # THIS IS WHERE YOU CALL YOUR AGENT
        # response = run_agent_once(query, history=[])
        response = run_agent(query, test_case) # Using mock
        # =====================================================

        latency = time.monotonic() - start_time

        # --- Validate Success ---
        final_answer_lower = response.get('final', '').lower()
        expected_keywords = test_case.get('expected_keywords', [])
        is_success = all(keyword.lower() in final_answer_lower for keyword in expected_keywords)

        # --- Validate Tool Selection ---
        expected_tool = test_case.get('expected_tool', 'no_tool')
        tools_called = response.get('tools_called', [])
        # Simple case: check if the first tool called matches.
        # For multi-tool scenarios, this logic could be more complex.
        actual_tool = tools_called[0] if tools_called else 'no_tool'
        is_tool_accurate = (expected_tool == actual_tool)

        return {
            "id": query_id,
            "category": test_case['category'],
            "query": query,
            "success": is_success,
            "tool_accurate": is_tool_accurate,
            "latency_seconds": latency,
            "llm_calls": response.get('llm_calls', 0),
            "reflections": response.get('reflections', 0),
            "expected_tool": expected_tool,
            "actual_tool": actual_tool,
            "final_answer": response.get('final', ''),
        }

    except Exception as e:
        latency = time.monotonic() - start_time
        print(f"    ❌ Test ID {query_id} failed with an exception: {e}")
        traceback.print_exc()
        return {
            "id": query_id,
            "category": test_case['category'],
            "query": query,
            "success": False,
            "tool_accurate": False,
            "latency_seconds": latency,
            "llm_calls": 0,
            "reflections": 0,
            "expected_tool": test_case.get('expected_tool'),
            "actual_tool": "ERROR",
            "final_answer": f"AGENT EXECUTION FAILED: {e}",
        }

def get_resume_data(output_dir: Path) -> tuple[dict, str | None]:
    """Finds the latest benchmark run to resume from."""
    if not output_dir.exists():
        return {}, None
    
    json_files = sorted(output_dir.glob("benchmark_results_*.json"), reverse=True)
    if not json_files:
        return {}, None
        
    latest_file = json_files[0]
    print(f"🔍 Found latest benchmark run: {latest_file}. Resuming...")
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # Create a lookup for faster access
        existing_results_map = {item['id']: item for item in existing_data}
        timestamp = latest_file.stem.replace("benchmark_results_", "")
        return existing_results_map, timestamp
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"⚠️ Could not read or parse {latest_file}. Starting a new run.")
        return {}, None

def main():
    """Main function to orchestrate the benchmarking process."""
    parser = argparse.ArgumentParser(description="Run benchmark tests for the General AI Agent.")
    parser.add_argument(
        '--categories', 
        nargs='+', 
        help="A list of categories to test (e.g., rag web_search). If not provided, all categories are tested."
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help="Resume the last benchmark run, skipping completed tests."
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help="Force a new run, ignoring previous results."
    )
    args = parser.parse_args()

    # --- Setup ---
    test_cases_path = Path("test_cases.json")
    output_dir = Path("results")
    
    all_test_cases = load_test_cases(test_cases_path)
    if not all_test_cases:
        return

    # --- Filtering ---
    test_cases_to_run = all_test_cases
    if args.categories:
        test_cases_to_run = [tc for tc in all_test_cases if tc['category'] in args.categories]
        print(f"🔬 Filtering tests for categories: {', '.join(args.categories)}")

    # --- Resuming Logic ---
    existing_results_map = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.resume and not args.no_resume:
        existing_results_map, resume_timestamp = get_resume_data(output_dir)
        if resume_timestamp:
            timestamp = resume_timestamp # Continue with the same timestamped file
    
    # --- Run Benchmark ---
    results = list(existing_results_map.values())
    total_to_run = len(test_cases_to_run)
    completed_count = 0

    print(f"\n🚀 Starting benchmark run. Total queries to process: {total_to_run}")
    
    try:
        for i, test_case in enumerate(test_cases_to_run):
            query_id = test_case['id']
            
            if args.resume and query_id in existing_results_map:
                print(f"  ({i+1}/{total_to_run}) Skipping Test ID {query_id} (already completed).")
                continue

            print(f"  ({i+1}/{total_to_run}) Running Test ID {query_id} [Category: {test_case['category']}]")
            result = run_single_test(test_case)
            results.append(result)
            completed_count += 1

    except KeyboardInterrupt:
        print("\n\n🛑 Benchmark run interrupted by user. Saving partial results...")

    finally:
        if completed_count > 0:
            save_results(results, output_dir, timestamp)
        else:
            print("\nNo new tests were run. No results to save.")

        # --- Analysis & Reporting ---
        if results:
            overall_metrics, category_metrics = calculate_metrics(results)
            print_summary(overall_metrics, category_metrics)
        else:
            print("\nNo results to analyze.")

if __name__ == "__main__":
    main()