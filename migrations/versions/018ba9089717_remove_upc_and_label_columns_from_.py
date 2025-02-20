"""remove upc and label columns from albums table

Revision ID: 018ba9089717
Revises: 6663af3dcdf7
Create Date: 2025-01-29 13:55:18.570304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '018ba9089717'
down_revision = '6663af3dcdf7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('albums', schema=None) as batch_op:
        batch_op.drop_constraint('albums_upc_key', type_='unique')
        batch_op.drop_column('label')
        batch_op.drop_column('upc')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('albums', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upc', sa.VARCHAR(length=30), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('label', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
        batch_op.create_unique_constraint('albums_upc_key', ['upc'])

    # ### end Alembic commands ###
