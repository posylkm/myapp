"""add investor_verified flag

Revision ID: dc8df8c8cb06
Revises: bb93d1df9eb9
Create Date: 2025-11-12 10:41:05.793193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc8df8c8cb06'
down_revision = 'bb93d1df9eb9'
branch_labels = None
depends_on = None



def upgrade():
    # 1) add column nullable with a default so existing rows get a value
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='0'))

    # 2) backfill explicitly (paranoia / cross-db safety)
    op.execute("UPDATE user SET is_verified = 0 WHERE is_verified IS NULL")

    # 3) make it NOT NULL; **keep** the DB default (don’t try to drop it on SQLite)
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('is_verified', existing_type=sa.Boolean(), nullable=False)
    # Do NOT call server_default=None on SQLite.

def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('is_verified')
