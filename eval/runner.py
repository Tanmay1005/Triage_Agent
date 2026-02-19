import json
import time
import os
from graph.pipeline import run_triage
from agents.dedup import init_vector_store, seed_vector_store
from eval.dataset import load_test_cases
from eval.metrics import compute_metrics, print_report


def evaluate_single(test_case: dict) -> dict:
    """Run a single test case and compare against expected output."""
    start = time.time()
    result = run_triage(test_case["input"])
    latency = time.time() - start

    expected = test_case["expected"]
    scores = {}

    # Decision accuracy
    if "decision" in expected:
        scores["decision"] = result.get("decision") == expected["decision"]

    # Validity check
    if "is_valid" in expected and result.get("parsed_ticket"):
        scores["is_valid"] = result["parsed_ticket"].is_valid == expected["is_valid"]

    # Duplicate detection
    if "is_duplicate" in expected and result.get("dedup_result"):
        scores["is_duplicate"] = result["dedup_result"].is_duplicate == expected["is_duplicate"]

    # Severity accuracy (only if ticket was created)
    if "severity" in expected and result.get("labeled_ticket"):
        scores["severity"] = result["labeled_ticket"].severity.value == expected["severity"]

    # Priority accuracy
    if "priority" in expected and result.get("labeled_ticket"):
        scores["priority"] = result["labeled_ticket"].priority.value == expected["priority"]

    # Issue type accuracy
    if "issue_type" in expected and result.get("labeled_ticket"):
        scores["issue_type"] = result["labeled_ticket"].issue_type.value == expected["issue_type"]

    # Team routing accuracy
    if "team" in expected and result.get("team_assignment"):
        scores["team"] = result["team_assignment"].team == expected["team"]

    # Label coverage (check if expected labels are a subset of predicted)
    if "labels_should_contain" in expected and result.get("labeled_ticket"):
        predicted_labels = set(l.lower() for l in result["labeled_ticket"].labels)
        expected_labels = set(l.lower() for l in expected["labels_should_contain"])
        scores["label_coverage"] = expected_labels.issubset(predicted_labels)

    return {
        "id": test_case["id"],
        "category": test_case.get("category", "unknown"),
        "scores": scores,
        "all_passed": all(scores.values()) if scores else False,
        "latency_s": round(latency, 2),
        "trace": result.get("trace", []),
    }


def run_full_eval(test_cases_path: str = None) -> dict:
    """Run all test cases and compute aggregate metrics."""
    # Ensure vector store is seeded
    collection = init_vector_store()
    seed_vector_store(collection)

    test_cases = load_test_cases(test_cases_path)
    results = []

    for i, tc in enumerate(test_cases):
        print(f"Running eval {i+1}/{len(test_cases)}: {tc['id']}...")
        result = evaluate_single(tc)
        results.append(result)
        status = "PASS" if result["all_passed"] else "FAIL"
        print(f"  {status} (latency: {result['latency_s']}s)")

    # Aggregate metrics
    metrics = compute_metrics(results)

    # Save results
    output = {"results": results, "metrics": metrics}
    results_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)

    print_report(metrics, results)
    return output


if __name__ == "__main__":
    run_full_eval()
