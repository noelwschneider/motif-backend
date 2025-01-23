"""add item type and date added to reviews table

Revision ID: 30c327f7cd91
Revises: 3575f2dec27c
Create Date: 2025-01-21 14:48:16.073335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30c327f7cd91'
down_revision = '3575f2dec27c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('item_type', sa.Enum('ALBUM', 'ARTIST', 'SONG', name='catalog_item_type_enum'), nullable=False))
        batch_op.add_column(sa.Column('item_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('date_added', sa.DateTime(timezone=True), nullable=False))
        batch_op.drop_constraint('reviews_album_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'albums', ['item_id'], ['id'])
        batch_op.drop_column('album_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('album_id', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('reviews_album_id_fkey', 'albums', ['album_id'], ['id'])
        batch_op.drop_column('date_added')
        batch_op.drop_column('item_id')
        batch_op.drop_column('item_type')

    # ### end Alembic commands ###
