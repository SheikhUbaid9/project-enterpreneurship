import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.message import EmailMessage
from app.models.thread import EmailThread
from shared.constants import DEFAULT_ADMIN_USER_ID, DEFAULT_MEMBER_USER_ID, DEFAULT_OWNER_USER_ID


settings = get_settings()


async def seed_mock_messages(session: AsyncSession) -> None:
    if not settings.mock_mode:
        return

    result = await session.execute(select(EmailMessage.id).limit(1))
    if result.scalar_one_or_none():
        return

    now = datetime.now(UTC)
    seed_users = [
        (DEFAULT_OWNER_USER_ID, "owner@inbox.local"),
        (DEFAULT_ADMIN_USER_ID, "admin@inbox.local"),
        (DEFAULT_MEMBER_USER_ID, "member@inbox.local"),
    ]

    priorities = ["urgent", "normal", "low"]

    for idx, (user_id, mailbox) in enumerate(seed_users):
        for i in range(settings.mock_seed_message_count):
            thread = EmailThread(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                subject=f"Mock Thread {idx + 1}-{i + 1}",
                participants_csv=f"client{i}@example.com,{mailbox}",
            )
            session.add(thread)
            await session.flush()

            incoming = EmailMessage(
                id=uuid.uuid4(),
                thread_id=thread.id,
                user_id=uuid.UUID(user_id),
                sender=f"client{i}@example.com",
                recipients_csv=mailbox,
                body=f"Hello {mailbox}, this is mock inbound message {i + 1}.",
                is_unread=True,
                direction="incoming",
                priority=priorities[i % len(priorities)],
                sent_at=now - timedelta(minutes=i * 5 + idx * 3),
            )
            session.add(incoming)

    await session.commit()
