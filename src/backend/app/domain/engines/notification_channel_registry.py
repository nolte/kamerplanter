from app.domain.interfaces.notification_channel import INotificationChannel


class NotificationChannelRegistry:
    _channels: dict[str, INotificationChannel] = {}

    @classmethod
    def register(cls, channel: INotificationChannel) -> None:
        cls._channels[channel.channel_key] = channel

    @classmethod
    def get(cls, channel_key: str) -> INotificationChannel | None:
        return cls._channels.get(channel_key)

    @classmethod
    def get_available(cls) -> list[INotificationChannel]:
        return list(cls._channels.values())

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._channels.keys())

    @classmethod
    def clear(cls) -> None:
        cls._channels = {}
