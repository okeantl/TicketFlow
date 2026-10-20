"""release stuck held seats

Revision ID: a32f34b36506
Revises: 961d2c1ba37d
Create Date: 2026-10-20 08:49:57.139225

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a32f34b36506"
down_revision: str | Sequence[str] | None = "961d2c1ba37d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Release seats stuck in HELD status."""
    op.execute("UPDATE seats SET status = 'AVAILABLE' WHERE status = 'HELD'")


def downgrade() -> None:
    """откатить нельзя, потому что после миграции неизвестно, какие места были HELD."""
