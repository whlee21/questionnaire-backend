"""initial

Revision ID: 6dcb37721b0e
Revises: 
Create Date: 2026-06-12 13:24:47.770988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6dcb37721b0e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. admin_users
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_admin_users_email"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"])

    # 2. push_devices
    op.create_table(
        "push_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("external_user_id", sa.String(255), nullable=True),
        sa.Column(
            "platform",
            sa.Enum("ios", "android", "web", name="platform"),
            nullable=False,
        ),
        sa.Column("fcm_token", sa.Text(), nullable=False),
        sa.Column("app_id", sa.String(255), nullable=True),
        sa.Column("app_version", sa.String(50), nullable=False),
        sa.Column("os_version", sa.String(50), nullable=True),
        sa.Column("device_model", sa.String(255), nullable=True),
        sa.Column("installation_id", sa.String(255), nullable=True),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "token_refreshed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_send_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_send_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalid_reason", sa.String(50), nullable=True),
        sa.UniqueConstraint("fcm_token", name="uq_push_devices_fcm_token"),
    )
    op.create_index("ix_push_devices_user_id", "push_devices", ["user_id"])
    op.create_index("ix_push_devices_external_user_id", "push_devices", ["external_user_id"])
    op.create_index("ix_push_devices_fcm_token", "push_devices", ["fcm_token"])
    op.create_index("ix_push_devices_installation_id", "push_devices", ["installation_id"])

    # 3. push_device_topics (FK to push_devices)
    op.create_table(
        "push_device_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "pending", "removed", name="topicstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "subscribed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["push_devices.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("device_id", "topic", name="uq_device_topic"),
    )
    op.create_index("ix_push_device_topics_device_id", "push_device_topics", ["device_id"])
    op.create_index("ix_push_device_topics_topic", "push_device_topics", ["topic"])

    # 4. push_send_events
    op.create_table(
        "push_send_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_summary", sa.String(500), nullable=False),
        sa.Column("payload_summary", sa.JSON(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_push_send_events_idempotency_key", "push_send_events", ["idempotency_key"])
    op.create_index("ix_push_send_events_created_at", "push_send_events", ["created_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("push_send_events")
    op.drop_table("push_device_topics")
    op.execute("DROP TYPE IF EXISTS topicstatus")
    op.drop_table("push_devices")
    op.execute("DROP TYPE IF EXISTS platform")
    op.drop_table("admin_users")
