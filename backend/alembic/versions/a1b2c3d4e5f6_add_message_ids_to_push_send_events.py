"""add message_ids to push_send_events

Revision ID: a1b2c3d4e5f6
Revises: 6dcb37721b0e
Create Date: 2026-06-16 15:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6dcb37721b0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "push_send_events",
        sa.Column("message_ids", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("push_send_events", "message_ids")
