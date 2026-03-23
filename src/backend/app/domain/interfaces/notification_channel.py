from abc import ABC, abstractmethod

from app.domain.models.notification import ChannelResult, Notification


class INotificationChannel(ABC):
    @property
    @abstractmethod
    def channel_key(self) -> str: ...

    @property
    @abstractmethod
    def supports_actions(self) -> bool: ...

    @property
    @abstractmethod
    def supports_batching(self) -> bool: ...

    @abstractmethod
    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult: ...

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        results: list[ChannelResult] = []
        for n in notifications:
            results.append(await self.send(n, channel_config))
        success = all(r.success for r in results)
        errors = [r.error for r in results if r.error]
        return ChannelResult(
            channel_key=self.channel_key,
            success=success,
            error="; ".join(errors) if errors else None,
        )

    async def health_check(self) -> bool:
        return True
