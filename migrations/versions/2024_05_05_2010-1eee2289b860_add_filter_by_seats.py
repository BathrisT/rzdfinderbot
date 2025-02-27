"""add filter by seats

Revision ID: 1eee2289b860
Revises: f83e260e938f
Create Date: 2024-05-05 20:10:52.463113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eee2289b860'
down_revision: Union[str, None] = 'f83e260e938f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trackings', sa.Column('sw_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('sid_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('plaz_seats_plaz_down_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('plaz_seats_plaz_up_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('plaz_side_down_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('plaz_side_up_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('cupe_up_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('trackings', sa.Column('cupe_down_enabled', sa.Boolean(), server_default='TRUE', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trackings', 'cupe_down_enabled')
    op.drop_column('trackings', 'cupe_up_enabled')
    op.drop_column('trackings', 'plaz_side_up_enabled')
    op.drop_column('trackings', 'plaz_side_down_enabled')
    op.drop_column('trackings', 'plaz_seats_plaz_up_enabled')
    op.drop_column('trackings', 'plaz_seats_plaz_down_enabled')
    op.drop_column('trackings', 'sid_enabled')
    op.drop_column('trackings', 'sw_enabled')
    # ### end Alembic commands ###
