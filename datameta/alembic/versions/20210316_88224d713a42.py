"""add files.access_token; add submissions.label; add metadata.example;

Revision ID: 88224d713a42
Revises: 657c9fe09a1c
Create Date: 2021-03-16 12:31:23.064667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88224d713a42'
down_revision = '657c9fe09a1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('access_token', sa.String(length=64), nullable=True))
    op.add_column('metadata', sa.Column('example', sa.Text(), nullable=True))
    op.execute("UPDATE metadata SET example='unknown'")
    op.alter_column('metadata', 'example', nullable=False)
    op.add_column('submissions', sa.Column('label', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('submissions', 'label')
    op.drop_column('metadata', 'example')
    op.drop_column('files', 'access_token')
    # ### end Alembic commands ###
