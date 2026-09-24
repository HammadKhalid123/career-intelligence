"""Add Gmail OAuth token storage."""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_gmail_tokens"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gmail_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("gmail_email", sa.String(length=255), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_type", sa.String(length=50), nullable=True, default="Bearer"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id"),
    )
    op.create_index("ix_gmail_connections_resume_id", "gmail_connections", ["resume_id"])


def downgrade() -> None:
    op.drop_index("ix_gmail_connections_resume_id", table_name="gmail_connections")
    op.drop_table("gmail_connections")
