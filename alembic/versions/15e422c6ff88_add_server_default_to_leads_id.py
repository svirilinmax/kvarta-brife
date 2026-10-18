"""add server_default to leads.id

Revision ID: 15e422c6ff88
Revises: 9927e7dd7772
Create Date: 2026-10-16 23:23:19.871876

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "15e422c6ff88"
down_revision: Union[str, None] = "9927e7dd7772"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("ALTER TABLE leads ALTER COLUMN id SET DEFAULT gen_random_uuid()")


def downgrade() -> None:
    op.execute("ALTER TABLE leads ALTER COLUMN id DROP DEFAULT")
