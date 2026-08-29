"""stage 2: ton topups, rental assets, p2p marketplace

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("target_username", sa.String(64), nullable=True))

    op.create_table(
        "rental_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("catalog_item_id", sa.Integer(), sa.ForeignKey("catalog_items.id"), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("access_payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="available"),
        sa.Column("current_order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("rented_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rental_assets_catalog_item_id", "rental_assets", ["catalog_item_id"])

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("asset_details", sa.JSON(), nullable=True),
        sa.Column("price_uzs", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending_review"),
        sa.Column("reviewed_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_listings_seller_id", "listings", ["seller_id"])

    op.create_table(
        "p2p_deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("escrow_uzs", sa.Numeric(14, 2), nullable=False),
        sa.Column("commission_uzs", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="awaiting_transfer"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_p2p_deals_listing_id", "p2p_deals", ["listing_id"])
    op.create_index("ix_p2p_deals_buyer_id", "p2p_deals", ["buyer_id"])

    op.create_table(
        "ton_topup_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False, server_default="topup"),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("expected_amount", sa.Numeric(20, 9), nullable=False),
        sa.Column("memo", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("tx_hash", sa.String(128), nullable=True),
        sa.Column("credited_uzs", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ton_topup_requests_user_id", "ton_topup_requests", ["user_id"])
    op.create_index("ix_ton_topup_requests_memo", "ton_topup_requests", ["memo"], unique=True)


def downgrade() -> None:
    op.drop_table("ton_topup_requests")
    op.drop_table("p2p_deals")
    op.drop_table("listings")
    op.drop_table("rental_assets")
    op.drop_column("orders", "target_username")
