"""provider role, moderation, reviews

Revision ID: 65753a7e42e3
Revises: ac7c592b360e
Create Date: 2026-05-18 15:15:02.658703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '65753a7e42e3'
down_revision: Union[str, None] = 'ac7c592b360e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


moderation_status_enum = sa.Enum(
    'PENDING', 'APPROVED', 'REJECTED', name='moderationstatus'
)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        moderation_status_enum.create(bind, checkfirst=True)
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PROVIDER'")

    op.create_table(
        'reviews',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('user_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('publication_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_reviews_rating_range'),
        sa.ForeignKeyConstraint(['publication_id'], ['publications.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'publication_id', name='uq_reviews_user_publication'),
    )
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reviews_id'), ['id'], unique=False)

    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'provider_id',
                sa.BigInteger().with_variant(sa.Integer(), 'sqlite'),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                'moderation_status',
                moderation_status_enum,
                nullable=False,
                server_default='APPROVED',
            )
        )
        batch_op.add_column(sa.Column('moderation_note', sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            'fk_publications_provider', 'users', ['provider_id'], ['id']
        )

    # Drop the server_default so application-level default takes over for new rows.
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.alter_column(
            'moderation_status', server_default=None, existing_type=moderation_status_enum
        )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('company_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('inn', sa.String(), nullable=True))

    if dialect == 'sqlite':
        # SQLite stores enum as VARCHAR; batch_alter_table on a VARCHAR column with
        # an enum-typed alter would recreate the table. Skip explicit role retype here.
        pass


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('inn')
        batch_op.drop_column('company_name')

    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.drop_constraint('fk_publications_provider', type_='foreignkey')
        batch_op.drop_column('moderation_note')
        batch_op.drop_column('moderation_status')
        batch_op.drop_column('provider_id')

    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reviews_id'))

    op.drop_table('reviews')

    if dialect == 'postgresql':
        moderation_status_enum.drop(bind, checkfirst=True)
