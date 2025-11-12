"""switch aum to band choices

Revision ID: 528f96087944
Revises: e85ed8ecca7b
Create Date: 2025-11-12 17:34:50.289228

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '528f96087944'
down_revision = 'e85ed8ecca7b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('aum_band', sa.String(length=20), nullable=True))

    # Map old float aum -> band
    conn = op.get_bind()
    # This works in SQLite and Postgres
    conn.execute(sa.text("""
        UPDATE "user"
        SET aum_band = CASE
            WHEN aum IS NULL THEN NULL
            WHEN aum < 50 THEN 'lt50'
            WHEN aum <= 100 THEN '50-100'
            ELSE 'gt100'
        END
    """))

    with op.batch_alter_table('user', schema=None) as batch_op:
        # drop old float column
        batch_op.drop_column('aum')
        # rename aum_band -> aum
        batch_op.alter_column('aum_band', new_column_name='aum', existing_type=sa.String(length=20), existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('aum_float', sa.Float(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE "user"
        SET aum_float =
            CASE aum
                WHEN 'lt50'   THEN 25
                WHEN '50-100' THEN 75
                WHEN 'gt100'  THEN 150
                ELSE NULL
            END
    """))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('aum')
        batch_op.alter_column('aum_float', new_column_name='aum', existing_type=sa.Float(), existing_nullable=True)

    # ### end Alembic commands ###
