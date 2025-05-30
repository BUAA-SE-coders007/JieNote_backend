"""增加作者名

Revision ID: a434b17f5caf
Revises: 4b9d22943860
Create Date: 2025-04-29 17:34:19.895192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'a434b17f5caf'
down_revision: Union[str, None] = '4b9d22943860'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('articleDB', 'author',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=300),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('articleDB', 'author',
               existing_type=sa.String(length=300),
               type_=mysql.VARCHAR(length=100),
               existing_nullable=False)
    # ### end Alembic commands ###
