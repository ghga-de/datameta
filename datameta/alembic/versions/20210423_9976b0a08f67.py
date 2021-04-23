"""add download token

Revision ID: 9976b0a08f67
Revises: 8399f5ae0845
Create Date: 2021-04-23 14:53:25.032188

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9976b0a08f67'
down_revision = '8399f5ae0845'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('downloadtokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('expires', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], name=op.f('fk_downloadtokens_file_id_files')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_downloadtokens')),
    sa.UniqueConstraint('uuid', name=op.f('uq_downloadtokens_uuid')),
    sa.UniqueConstraint('value', name=op.f('uq_downloadtokens_value'))
    )
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('downloadtokens')
    # ### end Alembic commands ###
