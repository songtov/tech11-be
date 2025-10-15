"""merge_heads

Revision ID: 4ddb57a0ca5c
Revises: da486a358923, e33e53747c55
Create Date: 2025-10-15 13:06:02.616676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ddb57a0ca5c'
down_revision: Union[str, Sequence[str], None] = ('da486a358923', 'e33e53747c55')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
