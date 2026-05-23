"""English Teacher agent for conversational English practice."""

from fluentia.agents.base import AgentDefinition
from fluentia.agents.base import FieldMetadata

english_teacher: AgentDefinition = AgentDefinition(
    name="english_teacher",
    display_name="FluentAI — English Coach",
    description=(
        "Practice conversational English with a friendly AI teacher. "
        "Get real-time corrections, explore guided topics, "
        "and adapt the session to your level."
    ),
    template_path="templates/english_teacher.j2",
    default_variables={
        "teacher_name": "Emma",
        "student_level": "B1 — Intermediate",
        "topic": "Free conversation",
        "correction_style": "End of Exchange",
        "guidelines": (
            "- Be warm, encouraging, and patient at all times\n"
            "- Always start your reply with 'You mean: [corrected phrase]' — never skip it\n"
            "- Ask open-ended follow-up questions to keep the conversation going\n"
            "- Praise the student's effort, not just correct answers\n"
            "- If the student seems frustrated, slow down and simplify\n"
            "- Introduce one new vocabulary word or expression per exchange when relevant\n"
            "- Keep responses concise — two to four sentences is usually enough\n"
            "- End each turn with a question to keep the student engaged"
        ),
    },
    field_metadata={
        "teacher_name": FieldMetadata(
            label="Teacher Name",
            placeholder="e.g. Emma",
            description="The name the teacher uses to introduce itself.",
            order=0,
        ),
        "student_level": FieldMetadata(
            label="Student Level",
            field_type="select",
            options=[
                "A1 — Beginner",
                "A2 — Elementary",
                "B1 — Intermediate",
                "B2 — Upper Intermediate",
                "C1 — Advanced",
                "C2 — Proficient",
            ],
            description="CEFR level. The teacher adapts vocabulary and complexity accordingly.",
            order=1,
        ),
        "topic": FieldMetadata(
            label="Conversation Topic",
            placeholder="e.g. Travel, Job interviews, Daily routines, Free conversation",
            description=(
                "The topic or scenario to practice. "
                "Use 'Free conversation' to let the student choose."
            ),
            order=2,
        ),
        "correction_style": FieldMetadata(
            label="Correction Style",
            field_type="select",
            options=["Conversational", "Immediate", "End of Exchange"],
            description=(
                "Conversational: errors echoed naturally in the reply. "
                "Immediate: corrected right away before continuing. "
                "End of Exchange: brief summary after each student turn."
            ),
            order=3,
        ),
        "guidelines": FieldMetadata(
            label="Teaching Guidelines",
            field_type="textarea",
            placeholder="Behavioral instructions for how the teacher should conduct the session...",
            rows=8,
            order=4,
        ),
    },
    enabled_tools=[],
    provider_settings=None,
)
