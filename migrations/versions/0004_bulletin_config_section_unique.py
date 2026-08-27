"""update bulletin_configs unique constraint to include section_id

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old unique constraint
    op.drop_constraint('unique_bulletin_config_per_level', 'bulletin_configs', type_='unique')
    # Add new unique constraint including section_id
    op.create_unique_constraint(
        'unique_bulletin_config_per_section_level',
        'bulletin_configs',
        ['school_id', 'section_id', 'level', 'academic_year']
    )


def downgrade():
    op.drop_constraint('unique_bulletin_config_per_section_level', 'bulletin_configs', type_='unique')
    op.create_unique_constraint(
        'unique_bulletin_config_per_level',
        'bulletin_configs',
        ['school_id', 'level', 'academic_year']
    )
