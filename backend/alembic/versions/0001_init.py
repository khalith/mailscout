"""initial tables

Revision ID: 0001_init
Revises:
Create Date: 2025-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM type once via raw SQL, only if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'uploadstatus') THEN
                CREATE TYPE uploadstatus AS ENUM ('queued', 'processing', 'completed', 'cancelled');
            END IF;
        END$$;
        """
    )

    # USERS
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # UPLOADS — reference the existing type by name only
    op.create_table(
        "uploads",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("total_count", sa.Integer(), server_default="0"),
        sa.Column("processed_count", sa.Integer(), server_default="0"),
        sa.Column(
            "status",
            # sa.Enum(
            #     "queued", "processing", "completed", "cancelled",
            #     name="uploadstatus",
            #     create_type=False  # <-- critical: don’t recreate type
            # ),
            sa.String(length=20),
            nullable=False
        ),
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
        sa.Column("score", sa.Integer(), server_default="0"),
        sa.Column("checks", sa.JSON(), server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("email_results")
    op.drop_table("uploads")
    op.drop_table("users")

    # Drop ENUM safely
    op.execute("DROP TYPE IF EXISTS uploadstatus")
