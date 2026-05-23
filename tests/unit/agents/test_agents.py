"""Tests for agent definitions and registry."""

from typing import Any

import pytest

from fluentia.agents.base import AgentDefinition
from fluentia.agents.base import FieldMetadata
from fluentia.agents.english_teacher import english_teacher
from fluentia.agents.registry import AgentRegistry


class TestFieldMetadata:
    def test_defaults(self):
        meta: FieldMetadata = FieldMetadata(label="Test")
        assert meta.label == "Test"
        assert meta.field_type == "text"
        assert meta.placeholder == ""
        assert meta.description == ""
        assert meta.options is None
        assert meta.rows == 6
        assert meta.order == 0

    def test_all_fields(self):
        meta: FieldMetadata = FieldMetadata(
            label="My Field",
            field_type="select",
            placeholder="Pick one",
            description="Help text",
            options=["a", "b"],
            rows=10,
            order=5,
        )
        assert meta.label == "My Field"
        assert meta.field_type == "select"
        assert meta.options == ["a", "b"]
        assert meta.rows == 10
        assert meta.order == 5


class TestAgentDefinitionSerializeFields:
    def test_with_metadata(self):
        agent: AgentDefinition = AgentDefinition(
            name="test",
            display_name="Test",
            description="A test agent",
            template_path="templates/english_teacher.j2",
            default_variables={"name": "Alice", "role": "tester"},
            field_metadata={
                "name": FieldMetadata(label="Name", order=1),
                "role": FieldMetadata(label="Role", order=0),
            },
        )
        fields: list[dict[str, Any]] = agent.serialize_fields()
        assert len(fields) == 2
        # Sorted by order: role (0) first, name (1) second
        assert fields[0]["key"] == "role"
        assert fields[0]["label"] == "Role"
        assert fields[1]["key"] == "name"
        assert fields[1]["label"] == "Name"
        assert fields[1]["default"] == "Alice"

    def test_without_metadata_auto_label(self):
        agent: AgentDefinition = AgentDefinition(
            name="test",
            display_name="Test",
            description="A test agent",
            template_path="templates/english_teacher.j2",
            default_variables={"agent_name": "Bob"},
        )
        fields: list[dict[str, Any]] = agent.serialize_fields()
        assert len(fields) == 1
        assert fields[0]["key"] == "agent_name"
        assert fields[0]["label"] == "Agent Name"

    def test_ordering(self):
        agent: AgentDefinition = AgentDefinition(
            name="test",
            display_name="Test",
            description="A test agent",
            template_path="templates/english_teacher.j2",
            default_variables={"a": "1", "b": "2", "c": "3"},
            field_metadata={
                "a": FieldMetadata(label="A", order=2),
                "b": FieldMetadata(label="B", order=0),
                "c": FieldMetadata(label="C", order=1),
            },
        )
        fields: list[dict[str, Any]] = agent.serialize_fields()
        assert [f["key"] for f in fields] == ["b", "c", "a"]


class TestRenderPromptHighlighted:
    def test_wraps_variable_values_in_spans(self):
        result: str = english_teacher.render_prompt_highlighted()
        assert '<span class="prompt-variable">Emma</span>' in result
        assert '<span class="prompt-variable">B1' in result

    def test_html_escapes_content(self):
        result: str = english_teacher.render_prompt_highlighted(
            {"teacher_name": "<script>alert(1)</script>"}
        )
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        assert '<span class="prompt-variable">' in result

    def test_static_text_not_wrapped(self):
        result: str = english_teacher.render_prompt_highlighted()
        # "STUDENT LEVEL" is static template text, not a variable
        assert '<span class="prompt-variable">STUDENT LEVEL' not in result


class TestEnglishTeacherAgent:
    def test_has_required_fields(self):
        assert english_teacher.name == "english_teacher"
        assert english_teacher.display_name == "English Teacher"

    def test_renders_prompt(self):
        prompt: str = english_teacher.render_prompt()
        assert len(prompt) > 0
        assert "Emma" in prompt

    def test_renders_with_overrides(self):
        prompt: str = english_teacher.render_prompt({"teacher_name": "John"})
        assert "John" in prompt

    def test_correction_style_conversational(self):
        prompt: str = english_teacher.render_prompt({"correction_style": "Conversational"})
        assert "echoing" in prompt or "naturally" in prompt

    def test_correction_style_immediate(self):
        prompt: str = english_teacher.render_prompt({"correction_style": "Immediate"})
        assert "immediately" in prompt or "Immediate" in prompt

    def test_correction_style_end_of_exchange(self):
        prompt: str = english_teacher.render_prompt({"correction_style": "End of Exchange"})
        assert "end" in prompt.lower() or "summary" in prompt.lower() or "quick note" in prompt

    def test_student_level_in_prompt(self):
        prompt: str = english_teacher.render_prompt({"student_level": "C1 — Advanced"})
        assert "C1" in prompt or "Advanced" in prompt

    def test_topic_in_prompt(self):
        prompt: str = english_teacher.render_prompt({"topic": "Job interviews"})
        assert "Job interviews" in prompt

    def test_config_fields(self):
        fields: list[str] = english_teacher.config_fields
        assert "teacher_name" in fields
        assert "student_level" in fields
        assert "topic" in fields
        assert "correction_style" in fields
        assert "guidelines" in fields

    def test_has_field_metadata(self):
        assert "teacher_name" in english_teacher.field_metadata
        assert "student_level" in english_teacher.field_metadata
        assert english_teacher.field_metadata["student_level"].field_type == "select"
        assert english_teacher.field_metadata["correction_style"].field_type == "select"
        assert english_teacher.field_metadata["guidelines"].field_type == "textarea"

    def test_student_level_options(self):
        meta: FieldMetadata = english_teacher.field_metadata["student_level"]
        assert meta.options is not None
        assert "A1 — Beginner" in meta.options
        assert "C2 — Proficient" in meta.options

    def test_correction_style_options(self):
        meta: FieldMetadata = english_teacher.field_metadata["correction_style"]
        assert meta.options is not None
        assert "Conversational" in meta.options
        assert "Immediate" in meta.options
        assert "End of Exchange" in meta.options

    def test_serialize_fields_count(self):
        fields: list[dict[str, Any]] = english_teacher.serialize_fields()
        assert len(fields) == 5

    def test_serialize_fields_order(self):
        fields: list[dict[str, Any]] = english_teacher.serialize_fields()
        keys: list[str] = [f["key"] for f in fields]
        assert keys[0] == "teacher_name"
        assert keys[1] == "student_level"
        assert keys[2] == "topic"
        assert keys[3] == "correction_style"
        assert keys[4] == "guidelines"

    def test_no_tools_enabled_by_default(self):
        assert english_teacher.enabled_tools == []


class TestAgentRegistry:
    def test_register_and_get(self):
        registry: AgentRegistry = AgentRegistry()
        registry.register(english_teacher)
        assert registry.get("english_teacher") is english_teacher

    def test_get_unknown_raises(self):
        registry: AgentRegistry = AgentRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list_agents(self):
        registry: AgentRegistry = AgentRegistry()
        registry.register(english_teacher)
        agents: list[AgentDefinition] = registry.list_agents()
        assert len(agents) == 1
        assert agents[0].name == "english_teacher"
