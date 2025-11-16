"""initial tables

Revision ID: 0001_init
Revises:
Create Date: 2025-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    # Create ENUM once
    upload_status_enum = ENUM(
        "queued", "processing", "completed", "cancelled",
        name="uploadstatus"
    )
    upload_status_enum.create(op.get_bind(), checkfirst=True)

    # USERS
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_admin", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # UPLOADS
    op.create_table(
        "uploads",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("total_count", sa.Integer(), default=0),
        sa.Column("processed_count", sa.Integer(), default=0),
        sa.Column("status", sa.Enum(
            "queued", "processing", "completed", "cancelled",
            name="uploadstatus",
        ), nullable=False),
        sa.Column("meta", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # EMAIL RESULTS
    op.create_table(
        "email_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("upload_id", sa.String(),
                  sa.ForeignKey("uploads.id", ondelete="CASCADE")),
        sa.Column("email", sa.String()),
        sa.Column("normalized", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("score", sa.Integer(), default=0),
        sa.Column("checks", sa.JSON(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("email_results")
    op.drop_table("uploads")
    op.drop_table("users")

    ENUM(name="uploadstatus").drop(op.get_bind(), checkfirst=True)
