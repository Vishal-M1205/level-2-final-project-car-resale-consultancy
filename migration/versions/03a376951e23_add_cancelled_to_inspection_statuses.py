"""add_cancelled_to_inspection_statuses

Revision ID: 03a376951e23
Revises: 6d3ff6f8a499
Create Date: 2026-11-04 17:07:10.139012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03a376951e23'
down_revision: Union[str, Sequence[str], None] = '6d3ff6f8a499'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('vehicle_inspection_status_check', 'vehicle_inspections', type_='check')
    op.create_check_constraint(
        'vehicle_inspection_status_check',
        'vehicle_inspections',
        "status IN ('PENDING', 'COMPLETED', 'CANCELLED')",
    )


def downgrade() -> None:
    op.drop_constraint('vehicle_inspection_status_check', 'vehicle_inspections', type_='check')
    op.create_check_constraint(
        'vehicle_inspection_status_check',
        'vehicle_inspections',
        "status IN ('PENDING', 'COMPLETED')",
    )
