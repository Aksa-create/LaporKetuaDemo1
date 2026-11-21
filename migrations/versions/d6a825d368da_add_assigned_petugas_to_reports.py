
"""add assigned petugas to reports

Revision ID: d6a825d368da
Revises:
Create Date: 2026-11-15 14:40:29.929082
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d6a825d368da"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("report", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "assigned_petugas_id",
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.create_index(
            "ix_report_assigned_petugas_id",
            ["assigned_petugas_id"],
            unique=False
        )

        batch_op.create_foreign_key(
            "report_assigned_petugas_id_fkey",
            "user",
            ["assigned_petugas_id"],
            ["id"]
        )


def downgrade():
    with op.batch_alter_table("report", schema=None) as batch_op:
        batch_op.drop_constraint(
            "report_assigned_petugas_id_fkey",
            type_="foreignkey"
        )

        batch_op.drop_index("ix_report_assigned_petugas_id")

        batch_op.drop_column("assigned_petugas_id")
