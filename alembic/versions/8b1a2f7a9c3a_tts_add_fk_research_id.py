"""tts: add FK to research_id

Revision ID: 8b1a2f7a9c3a
Revises: e30d316da0b6
Create Date: 2025-10-15
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8b1a2f7a9c3a"
down_revision = "e30d316da0b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("tts", schema=None) as batch_op:
        # Create FK from tts.research_id -> research.id
        batch_op.create_foreign_key(
            "fk_tts_research_id", "research", ["research_id"], ["id"]
        )
        # Optionally enforce one TTS per research by uncommenting below
        # batch_op.create_unique_constraint("uq_tts_research_id", ["research_id"])


def downgrade() -> None:
    with op.batch_alter_table("tts", schema=None) as batch_op:
        # If unique was created during upgrade, drop it first
        # batch_op.drop_constraint("uq_tts_research_id", type_="unique")
        batch_op.drop_constraint("fk_tts_research_id", type_="foreignkey")
