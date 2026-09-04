import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda_ingest"))

from extract_intelligence_tool import find_act_file


def test_exact_act_name_matches():
    assert find_act_file("modern slavery") == "legislation/modern_slavery_2015.txt"
    assert find_act_file("bribery") == "legislation/bribery_2010.txt"


def test_partial_name_matches():
    assert find_act_file("the Modern Slavery Act 2015") == "legislation/modern_slavery_2015.txt"


def test_case_insensitive():
    assert find_act_file("MODERN SLAVERY") == "legislation/modern_slavery_2015.txt"


def test_blank_input_returns_none():
    assert find_act_file("") is None


def test_unknown_act_returns_none():
    assert find_act_file("data breach nonsense act") is None
