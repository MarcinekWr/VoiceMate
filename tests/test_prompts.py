import pytest
from src.logic.llm_podcast import load_prompt_template
from src.logic.llm_podcast import PROMPT_PATHS

def test_load_prompt_template_scientific():
    template = load_prompt_template("scientific")
    assert "{input_text}" in template.template  
    assert "{plan_text}" in template.template

def test_load_prompt_template_casual():
    template = load_prompt_template("casual")
    assert "{input_text}" in template.template
    assert "{plan_text}" in template.template

def test_load_prompt_template_plan():
    template = load_prompt_template("plan")
    assert "{input_text}" in template.template

def test_load_prompt_template_invalid_style():
    with pytest.raises(ValueError):
        load_prompt_template("funny") 

def test_load_prompt_template_missing_file(tmp_path, monkeypatch):

    monkeypatch.setitem(PROMPT_PATHS, "plan", tmp_path / "missing.txt")

    with pytest.raises(FileNotFoundError):
        load_prompt_template("plan")
