import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import EmailMessage
from app.models.thread import EmailThread
from shared.models import Message, MessageDirection, Platform, Priority, ThreadDetail


def _csv_to_list(value: str) -> list[str]:
    if not value:
        return []
    return [item for item in value.split(",") if item]


def _list_to_csv(value: list[str]) -> str:
    return ",".join(v.strip() for v in value if v.strip())


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_unread_messages(self, user_id: str, limit: int) -> list[Message]:
        stmt = (
            select(EmailMessage, EmailThread)
            .join(EmailThread, EmailThread.id == EmailMessage.thread_id)
            .where(EmailMessage.user_id == uuid.UUID(user_id), EmailMessage.is_unread.is_(True))
            .order_by(EmailMessage.sent_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [self._to_message(row.EmailMessage, row.EmailThread) for row in rows]

    async def get_thread(self, user_id: str, thread_id: str) -> ThreadDetail | None:
        thread_stmt = select(EmailThread).where(
            EmailThread.id == uuid.UUID(thread_id),
            EmailThread.user_id == uuid.UUID(user_id),
        )
        thread_result = await self.session.execute(thread_stmt)
        thread = thread_result.scalar_one_or_none()
        if not thread:
            return None

        messages_stmt = (
            select(EmailMessage)
            .where(EmailMessage.thread_id == thread.id, EmailMessage.user_id == uuid.UUID(user_id))
            .order_by(EmailMessage.sent_at.asc())
        )
        messages_result = await self.session.execute(messages_stmt)
        messages = list(messages_result.scalars().all())

        unread_count_stmt = select(func.count(EmailMessage.id)).where(
            EmailMessage.thread_id == thread.id,
            EmailMessage.user_id == uuid.UUID(user_id),
            EmailMessage.is_unread.is_(True),
        )
        unread_count_result = await self.session.execute(unread_count_stmt)
        unread_count = int(unread_count_result.scalar() or 0)

        return ThreadDetail(
            id=str(thread.id),
            user_id=str(thread.user_id),
            platform=Platform.EMAIL,
            subject=thread.subject,
            participants=_csv_to_list(thread.participants_csv),
            unread_count=unread_count,
            messages=[self._to_message(message, thread) for message in messages],
        )

    async def send_reply(self, user_id: str, message_id: str, body: str) -> Message:
        msg_stmt = (
            select(EmailMessage, EmailThread)
            .join(EmailThread, EmailThread.id == EmailMessage.thread_id)
            .where(EmailMessage.id == uuid.UUID(message_id), EmailMessage.user_id == uuid.UUID(user_id))
        )
        result = await self.session.execute(msg_stmt)
        row = result.first()
        if not row:
            raise ValueError("Message not found")

        original = row.EmailMessage
        thread = row.EmailThread

        original.is_unread = False

        reply = EmailMessage(
            thread_id=thread.id,
            user_id=uuid.UUID(user_id),
            sender="assistant@inbox.local",
            recipients_csv=_list_to_csv(_csv_to_list(original.recipients_csv) or [original.sender]),
            body=body,
            is_unread=False,
            direction=MessageDirection.OUTGOING.value,
            priority=Priority.NORMAL.value,
            sent_at=datetime.now(UTC),
        )
        self.session.add(reply)
        thread.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(reply)

        return self._to_message(reply, thread)

    async def send_message(
        self,
        user_id: str,
        subject: str | None,
        recipients: list[str],
        body: str,
        thread_id: str | None = None,
    ) -> Message:
        thread: EmailThread | None = None
        if thread_id:
            stmt = select(EmailThread).where(
                EmailThread.id == uuid.UUID(thread_id),
                EmailThread.user_id == uuid.UUID(user_id),
            )
            result = await self.session.execute(stmt)
            thread = result.scalar_one_or_none()

        if not thread:
            thread = EmailThread(
                user_id=uuid.UUID(user_id),
                subject=subject,
                participants_csv=_list_to_csv(recipients),
            )
            self.session.add(thread)
            await self.session.flush()

        message = EmailMessage(
            thread_id=thread.id,
            user_id=uuid.UUID(user_id),
            sender="assistant@inbox.local",
            recipients_csv=_list_to_csv(recipients),
            body=body,
            is_unread=False,
            direction=MessageDirection.OUTGOING.value,
            priority=Priority.NORMAL.value,
            sent_at=datetime.now(UTC),
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        await self.session.refresh(thread)
        return self._to_message(message, thread)

    async def mark_as_read(self, user_id: str, message_id: str) -> Message:
        stmt = (
            select(EmailMessage, EmailThread)
            .join(EmailThread, EmailThread.id == EmailMessage.thread_id)
            .where(EmailMessage.id == uuid.UUID(message_id), EmailMessage.user_id == uuid.UUID(user_id))
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            raise ValueError("Message not found")

        message = row.EmailMessage
        thread = row.EmailThread
        message.is_unread = False
        await self.session.commit()
        await self.session.refresh(message)
        return self._to_message(message, thread)

    def _to_message(self, message: EmailMessage, thread: EmailThread) -> Message:
        return Message(
            id=str(message.id),
            thread_id=str(message.thread_id),
            user_id=str(message.user_id),
            platform=Platform.EMAIL,
            sender=message.sender,
            recipients=_csv_to_list(message.recipients_csv),
            subject=thread.subject,
            body=message.body,
            is_unread=message.is_unread,
            direction=MessageDirection(message.direction),
            priority=Priority(message.priority),
            sent_at=message.sent_at,
        )
