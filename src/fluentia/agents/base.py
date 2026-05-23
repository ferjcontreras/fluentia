"""Agent definition dataclass."""

import html
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import jinja2

# Null-byte markers that cannot appear in user content or templates.
_HL_START: str = "\x00HS\x00"
_HL_END: str = "\x00HE\x00"


@dataclass(frozen=True)
class FieldMetadata:
    """Rendering hints for a configurable agent field."""

    label: str
    field_type: str = "text"
    placeholder: str = ""
    description: str = ""
    options: list[str] | None = None
    rows: int = 6
    order: int = 0


@dataclass(frozen=True)
class AgentDefinition:
    """Defines an agent's behavior through configuration, not code."""

    name: str
    display_name: str
    description: str
    template_path: str
    default_variables: dict[str, Any] = field(default_factory=dict)
    enabled_tools: list[str] = field(default_factory=list)
    provider_settings: dict[str, Any] | None = field(default=None)
    field_metadata: dict[str, FieldMetadata] = field(default_factory=dict)

    @staticmethod
    def _escape_braces(value: Any) -> Any:
        """Escape lone curly braces in string values.

        Prevents Jinja2 and downstream template engines (e.g. Google ADK) from
        interpreting {word} as variables. Single { becomes {{ and single } becomes }}.
        Already-doubled {{ and }} are left untouched.
        """
        if not isinstance(value, str):
            return value
        # Replace single braces that are not already doubled
        value = re.sub(r"(?<!\{)\{(?!\{)", "{{", value)
        value = re.sub(r"(?<!\})\}(?!\})", "}}", value)
        return value

    def render_prompt(self, user_variables: dict[str, Any] | None = None) -> str:
        """Render the prompt template with merged variables.

        User-provided variables override defaults. Unknown variables are ignored.
        """
        merged: dict[str, Any] = {**self.default_variables}
        if user_variables:
            # Only merge keys that exist in default_variables or the template
            for key, value in user_variables.items():
                merged[key] = value

        # Escape lone braces in all string values so downstream engines
        # (Jinja2 second pass, Google ADK) do not interpret {word} as variables.
        merged = {k: self._escape_braces(v) for k, v in merged.items()}

        template_file: Path = Path(__file__).parent / self.template_path
        template_str: str = template_file.read_text(encoding="utf-8")

        env: jinja2.Environment = jinja2.Environment(
            undefined=jinja2.Undefined,
            autoescape=False,  # noqa: S701
        )
        template: jinja2.Template = env.from_string(template_str)
        return template.render(**merged)

    def render_prompt_highlighted(self, user_variables: dict[str, Any] | None = None) -> str:
        """Render the prompt as HTML with variable values wrapped in spans.

        All content is HTML-escaped. Substituted values are wrapped in
        ``<span class="prompt-variable">`` for visual distinction.
        """
        merged: dict[str, Any] = {**self.default_variables}
        if user_variables:
            for key, value in user_variables.items():
                merged[key] = value

        # Wrap each value with null-byte markers before rendering
        marked: dict[str, str] = {k: f"{_HL_START}{v}{_HL_END}" for k, v in merged.items()}

        template_file: Path = Path(__file__).parent / self.template_path
        template_str: str = template_file.read_text(encoding="utf-8")

        env: jinja2.Environment = jinja2.Environment(
            undefined=jinja2.Undefined,
            autoescape=False,  # noqa: S701
        )
        template: jinja2.Template = env.from_string(template_str)
        rendered: str = template.render(**marked)

        # HTML-escape the entire output, then replace markers with spans
        escaped: str = html.escape(rendered)
        result: str = escaped.replace(_HL_START, '<span class="prompt-variable">').replace(
            _HL_END, "</span>"
        )
        return result

    @property
    def config_fields(self) -> list[str]:
        """Return the list of configurable fields for the frontend."""
        return list(self.default_variables.keys())

    def serialize_fields(self) -> list[dict[str, Any]]:
        """Serialize field metadata for the API response, sorted by order."""
        fields: list[dict[str, Any]] = []
        for key, default_value in self.default_variables.items():
            meta: FieldMetadata = self.field_metadata.get(
                key, FieldMetadata(label=key.replace("_", " ").title())
            )
            fields.append(
                {
                    "key": key,
                    "label": meta.label,
                    "field_type": meta.field_type,
                    "placeholder": meta.placeholder,
                    "description": meta.description,
                    "default": default_value,
                    "options": meta.options,
                    "rows": meta.rows,
                    "order": meta.order,
                }
            )
        fields.sort(key=lambda f: f["order"])
        return fields
