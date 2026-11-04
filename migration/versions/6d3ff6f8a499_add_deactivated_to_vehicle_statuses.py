"""add_deactivated_to_vehicle_statuses

Revision ID: 6d3ff6f8a499
Revises: 0af8ac14a826
Create Date: 2026-11-04 14:53:28.843425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d3ff6f8a499'
down_revision: Union[str, Sequence[str], None] = '0af8ac14a826'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('vehicle_status_check', 'vehicles', type_='check')
    op.create_check_constraint(
        'vehicle_status_check',
        'vehicles',
        "status IN ('submitted', 'approved', 'rejected', 'sold', 'deactivated')",
    )


def downgrade() -> None:
    op.drop_constraint('vehicle_status_check', 'vehicles', type_='check')
    op.create_check_constraint(
        'vehicle_status_check',
        'vehicles',
        "status IN ('submitted', 'approved', 'rejected', 'sold')",
    )
