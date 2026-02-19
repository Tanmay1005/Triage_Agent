def compute_metrics(results: list) -> dict:
    """Compute per-dimension accuracy metrics from eval results."""
    dimensions = [
        "decision",
        "severity",
        "priority",
        "issue_type",
        "team",
        "is_valid",
        "is_duplicate",
        "label_coverage",
    ]

    metrics = {}
    for dim in dimensions:
        relevant = [r for r in results if dim in r["scores"]]
        if relevant:
            correct = sum(1 for r in relevant if r["scores"][dim])
            metrics[dim] = {
                "accuracy": round(correct / len(relevant), 3),
                "correct": correct,
                "total": len(relevant),
            }

    # Overall pass rate
    metrics["overall_pass_rate"] = round(
        sum(1 for r in results if r["all_passed"]) / len(results), 3
    ) if results else 0.0

    # Average latency
    metrics["avg_latency_s"] = round(
        sum(r["latency_s"] for r in results) / len(results), 2
    ) if results else 0.0

    # Per-category breakdown
    categories = set(r["category"] for r in results)
    metrics["by_category"] = {}
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        passed = sum(1 for r in cat_results if r["all_passed"])
        metrics["by_category"][cat] = {
            "pass_rate": round(passed / len(cat_results), 3),
            "total": len(cat_results),
        }

    return metrics


def print_report(metrics: dict, results: list):
    """Print a human-readable eval report."""
    print("\n" + "=" * 60)
    print("SENTINEL EVAL REPORT")
    print("=" * 60)

    print(f"\nOverall pass rate: {metrics['overall_pass_rate']*100:.1f}%")
    print(f"Average latency: {metrics['avg_latency_s']}s")

    print("\nPer-dimension accuracy:")
    for dim in ["decision", "severity", "issue_type", "team", "is_duplicate", "is_valid"]:
        if dim in metrics:
            m = metrics[dim]
            print(f"  {dim:20s}: {m['accuracy']*100:.1f}% ({m['correct']}/{m['total']})")

    print("\nPer-category pass rate:")
    for cat, m in sorted(metrics.get("by_category", {}).items()):
        print(f"  {cat:25s}: {m['pass_rate']*100:.1f}% ({m['total']} cases)")

    # Failures
    failures = [r for r in results if not r["all_passed"]]
    if failures:
        print(f"\nFailed cases ({len(failures)}):")
        for f in failures:
            failed_dims = [k for k, v in f["scores"].items() if not v]
            print(f"  {f['id']}: failed on {', '.join(failed_dims)}")
