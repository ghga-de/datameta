"""add new field users.site_read

Revision ID: 692b55499382
Revises: 8399f5ae0845
Create Date: 2021-04-20 22:19:38.003039

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '692b55499382'
down_revision = '8399f5ae0845'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('site_read', sa.BOOLEAN(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'site_read')
    # ### end Alembic commands ###
