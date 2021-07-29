"""add group_view to users

Revision ID: d10fbd865b76
Revises: f6a70402119f
Create Date: 2021-07-28 21:07:02.727561

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd10fbd865b76'
down_revision = 'f6a70402119f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('group_view', sa.Boolean(create_constraint=False), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'group_view')
    # ### end Alembic commands ###
