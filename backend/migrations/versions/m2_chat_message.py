"""Add ChatMessage

Revision ID: add_chat_message
Revises: c185ef21d784
Create Date: 2024-05-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_chat_message'
down_revision: Union[str, None] = 'c185ef21d784'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_messages',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('notebook_id', sa.String(), nullable=True),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('citations', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('chat_messages')
