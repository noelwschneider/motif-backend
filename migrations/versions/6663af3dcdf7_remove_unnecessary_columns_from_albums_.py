"""remove unnecessary columns from albums, tracks table

Revision ID: 6663af3dcdf7
Revises: 98c42912bdaa
Create Date: 2025-01-29 13:53:32.040068

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6663af3dcdf7'
down_revision = '98c42912bdaa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('albums', schema=None) as batch_op:
        batch_op.drop_column('duration_ms')
        batch_op.drop_column('explicit')

    with op.batch_alter_table('catalog_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_date', sa.DateTime(timezone=True), nullable=False))
        batch_op.alter_column('spotify_artist_id',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)
        batch_op.create_index(batch_op.f('ix_catalog_items_spotify_id'), ['spotify_id'], unique=False)
        batch_op.create_foreign_key(None, 'artists', ['spotify_artist_id'], ['spotify_id'])
        batch_op.drop_column('item_id')
        batch_op.drop_column('item_type')

    with op.batch_alter_table('catalogs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('comment', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_private', sa.Boolean(), nullable=False))
        batch_op.drop_column('description')
        batch_op.drop_column('private')

    with op.batch_alter_table('tracks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration_ms', sa.Integer(), nullable=True))
        batch_op.drop_constraint('tracks_isrc_key', type_='unique')
        batch_op.drop_constraint('tracks_iswc_key', type_='unique')
        batch_op.drop_column('duration')
        batch_op.drop_column('isrc')
        batch_op.drop_column('iswc')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tracks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('iswc', sa.VARCHAR(length=30), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('isrc', sa.VARCHAR(length=30), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('duration', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_unique_constraint('tracks_iswc_key', ['iswc'])
        batch_op.create_unique_constraint('tracks_isrc_key', ['isrc'])
        batch_op.drop_column('duration_ms')

    with op.batch_alter_table('catalogs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('private', sa.BOOLEAN(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.drop_column('is_private')
        batch_op.drop_column('comment')

    with op.batch_alter_table('catalog_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('item_type', postgresql.ENUM('artist', 'album', 'track', name='music_item_type_enum'), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('item_id', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_catalog_items_spotify_id'))
        batch_op.alter_column('spotify_artist_id',
               existing_type=sa.VARCHAR(length=128),
               nullable=True)
        batch_op.drop_column('updated_date')

    with op.batch_alter_table('albums', schema=None) as batch_op:
        batch_op.add_column(sa.Column('explicit', sa.BOOLEAN(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('duration_ms', sa.INTEGER(), autoincrement=False, nullable=True))

    # ### end Alembic commands ###
