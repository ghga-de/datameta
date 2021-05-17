"""Added tables Service and ServiceExecution

Revision ID: 6e77c5e9111b
Revises: 4cf970aec869
Create Date: 2021-04-30 14:36:15.510580

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6e77c5e9111b'
down_revision = '4cf970aec869'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('services',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('site_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_services')),
    sa.UniqueConstraint('uuid', name=op.f('uq_services_uuid'))
    )
    op.create_index(op.f('ix_services_site_id'), 'services', ['site_id'], unique=True)
    op.create_table('service_user',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('service_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['service_id'], ['services.id'], name=op.f('fk_service_user_service_id_services')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_service_user_user_id_users'))
    )
    op.create_table('serviceecexution',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('service_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('metadataset_id', sa.Integer(), nullable=False),
    sa.Column('datetime', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['metadataset_id'], ['metadatasets.id'], name=op.f('fk_serviceecexution_metadataset_id_metadatasets')),
    sa.ForeignKeyConstraint(['service_id'], ['services.id'], name=op.f('fk_serviceecexution_service_id_services')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_serviceecexution_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_serviceecexution'))
    )
    op.add_column('metadata', sa.Column('service_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_metadata_service_id_services'), 'metadata', 'services', ['service_id'], ['id'])
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_metadata_service_id_services'), 'metadata', type_='foreignkey')
    op.drop_column('metadata', 'service_id')
    op.drop_table('serviceecexution')
    op.drop_table('service_user')
    op.drop_index(op.f('ix_services_site_id'), table_name='services')
    op.drop_table('services')
    # ### end Alembic commands ###