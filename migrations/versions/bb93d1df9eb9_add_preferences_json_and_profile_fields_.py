"""add preferences_json and profile fields to user

Revision ID: bb93d1df9eb9
Revises: 75bc4a440cf4
Create Date: 2025-11-10 13:32:10.138731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb93d1df9eb9'
down_revision = '75bc4a440cf4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('preferences_json', sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    # Optional: drop server default so future inserts rely on ORM default
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('preferences_json', server_default=None)

def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('preferences_json')
