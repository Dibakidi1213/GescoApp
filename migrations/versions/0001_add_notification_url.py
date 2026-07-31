"""add notification.url column

Revision ID: 0001_add_notification_url
Revises: 
Create Date: 2026-06-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_notification_url'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notifications', sa.Column('url', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('notifications', 'url')
