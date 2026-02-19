import json
import os

_TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.json")


def load_test_cases(path: str = None) -> list:
    """Load eval test cases from JSON file."""
    if path is None:
        path = _TEST_CASES_PATH
    with open(path) as f:
        return json.load(f)
