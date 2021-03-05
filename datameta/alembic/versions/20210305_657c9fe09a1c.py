"""mdat site_unique and submission_unique

Revision ID: 657c9fe09a1c
Revises: 4ac6c2e47767
Create Date: 2021-03-05 21:54:48.606951

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '657c9fe09a1c'
down_revision = '4ac6c2e47767'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('metadata', sa.Column('site_unique', sa.Boolean(create_constraint=False), nullable=True))
    op.add_column('metadata', sa.Column('submission_unique', sa.Boolean(create_constraint=False), nullable=True))
    op.execute("UPDATE metadata SET site_unique=false, submission_unique=false")
    op.alter_column('metadata', 'site_unique', nullable=False)
    op.alter_column('metadata', 'submission_unique', nullable=False)

def downgrade():
    op.drop_column('metadata', 'submission_unique')
    op.drop_column('metadata', 'site_unique')
