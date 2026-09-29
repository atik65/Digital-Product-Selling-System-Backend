"""update_site_settings_telegram_and_youtube_urls

Revision ID: cd20c9669aaa
Revises: dd05229b6bb2
Create Date: 2026-09-29 16:50:58.582518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd20c9669aaa'
down_revision: Union[str, Sequence[str], None] = 'dd05229b6bb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('site_settings', 'telegram_url', new_column_name='telegram_channel_url')
    op.add_column('site_settings', sa.Column('telegram_support_url', sa.String(), nullable=True))
    op.add_column('site_settings', sa.Column('youtube_channel_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('site_settings', 'youtube_channel_url')
    op.drop_column('site_settings', 'telegram_support_url')
    op.alter_column('site_settings', 'telegram_channel_url', new_column_name='telegram_url')
