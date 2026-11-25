"""Use neutral defaults for new business settings; preserve existing client data.

Revision ID: 003_safe_business_defaults
Revises: 002_post_product_links_and_comments
"""
from alembic import op
import sqlalchemy as sa

revision = "003_safe_business_defaults"
down_revision = "002_post_product_links_and_comments"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("business_settings") as batch:
        for name in ("business_name", "tagline", "store_timings"):
            batch.alter_column(name, existing_type=sa.String(255), server_default="")
        batch.alter_column("auto_reply_enabled", existing_type=sa.Boolean(), server_default=sa.false())
        for purity in ("24k", "22k", "18k"):
            batch.alter_column(f"gold_rate_{purity}_per_10g", existing_type=sa.Float(), server_default="0")


def downgrade():
    with op.batch_alter_table("business_settings") as batch:
        batch.alter_column("business_name", existing_type=sa.String(255), server_default="Luxe Aura Jewels")
        batch.alter_column("tagline", existing_type=sa.String(255), server_default="Timeless Elegance & Certified Fine Jewellery")
        batch.alter_column("store_timings", existing_type=sa.String(255), server_default=None)
        batch.alter_column("auto_reply_enabled", existing_type=sa.Boolean(), server_default=sa.true())
        for purity, rate in (("24k", "78500.0"), ("22k", "72000.0"), ("18k", "58900.0")):
            batch.alter_column(f"gold_rate_{purity}_per_10g", existing_type=sa.Float(), server_default=rate)
