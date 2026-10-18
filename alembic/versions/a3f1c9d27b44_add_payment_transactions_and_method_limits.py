"""add payment_transactions ledger and payment method transaction limits

Revision ID: a3f1c9d27b44
Revises: c5e8c1f86067
Create Date: 2026-10-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f1c9d27b44"
down_revision: Union[str, Sequence[str], None] = "c5e8c1f86067"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "payment_methods",
        sa.Column("daily_transaction_limit", sa.Integer(), nullable=True),
    )
    op.add_column(
        "payment_methods",
        sa.Column("monthly_transaction_limit", sa.Integer(), nullable=True),
    )

    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_method_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("transaction_id", sa.String(), nullable=False),
        sa.Column("sender_number", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("transaction_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["payment_method_id"], ["payment_methods.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_type", "source_id", name="uq_payment_tx_source"),
    )
    op.create_index(
        op.f("ix_payment_transactions_id"), "payment_transactions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_payment_transactions_payment_method_id"),
        "payment_transactions",
        ["payment_method_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_source_type"),
        "payment_transactions",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_user_id"),
        "payment_transactions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_transaction_id"),
        "payment_transactions",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_transaction_at"),
        "payment_transactions",
        ["transaction_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_is_deleted"),
        "payment_transactions",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        "ix_payment_tx_method_time",
        "payment_transactions",
        ["payment_method_id", "transaction_at"],
        unique=False,
    )

    # Backfill history from payments / top-ups that were already successful.
    op.execute(
        sa.text(
            """
            INSERT INTO payment_transactions
                (payment_method_id, source_type, source_id, user_id,
                 transaction_id, sender_number, amount, transaction_at)
            SELECT payment_method_id, 'ORDER_PAYMENT', id, user_id,
                   transaction_id, sender_number, amount,
                   COALESCE(verified_at, created_at)
            FROM payments
            WHERE status = 'VERIFIED' AND is_deleted = false
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO payment_transactions
                (payment_method_id, source_type, source_id, user_id,
                 transaction_id, sender_number, amount, transaction_at)
            SELECT payment_method_id, 'WALLET_TOPUP', id, user_id,
                   transaction_id, sender_number, amount,
                   COALESCE(verified_at, created_at)
            FROM topups
            WHERE status = 'APPROVED' AND is_deleted = false
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_payment_tx_method_time", table_name="payment_transactions")
    op.drop_index(
        op.f("ix_payment_transactions_is_deleted"), table_name="payment_transactions"
    )
    op.drop_index(
        op.f("ix_payment_transactions_transaction_at"),
        table_name="payment_transactions",
    )
    op.drop_index(
        op.f("ix_payment_transactions_transaction_id"),
        table_name="payment_transactions",
    )
    op.drop_index(
        op.f("ix_payment_transactions_user_id"), table_name="payment_transactions"
    )
    op.drop_index(
        op.f("ix_payment_transactions_source_type"), table_name="payment_transactions"
    )
    op.drop_index(
        op.f("ix_payment_transactions_payment_method_id"),
        table_name="payment_transactions",
    )
    op.drop_index(op.f("ix_payment_transactions_id"), table_name="payment_transactions")
    op.drop_table("payment_transactions")
    op.drop_column("payment_methods", "monthly_transaction_limit")
    op.drop_column("payment_methods", "daily_transaction_limit")
