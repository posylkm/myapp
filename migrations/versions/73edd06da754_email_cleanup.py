"""email cleanup

Revision ID: 73edd06da754
Revises: dc8df8c8cb06
Create Date: 2025-11-12 12:51:17.514455

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73edd06da754'
down_revision = 'dc8df8c8cb06'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_user_email_ci",
        "user",
        [sa.text("lower(email)")],
        unique=True
    )

def downgrade():
    op.drop_index("uq_user_email_ci", table_name="user")
    # ### end Alembic commands ###
