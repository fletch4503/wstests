import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.template.loader import render_to_string, get_template
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Called on connection.
        # To accept the connection call:
        # cache.clear()
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            # self.group_name = f"user_{user.id}"
            self.group_name = f"user_{user.id}_notifications"
            logger.info(
                "Consumers Connect --> Group Name: %s, Channel Name: %s",
                self.group_name,
                self.channel_name,
            )
            # Join room group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()  # To accept the connection
            # Check for login notification flag after accepting
            if cache.get(f"user_{user.id}_login_notification"):
                # Send login notification
                html = get_template("core/partials/notifications.html").render(
                    context={
                        "username": user.username,
                        "title": "Добро пожаловать!",
                        "message": f"Пользователь {user.username} вошел в систему.",
                        "level": "info",
                    }
                )
                # message = render_to_string(
                #     "core/partials/notifications.html",
                #     # message =
                #     {
                #         "username": user.username,
                #         "title": "Добро пожаловать!",
                #         "message": f"Пользователь {user.username} вошел в систему.",
                #         "level": "info",
                #     },
                # )
                try:
                    # await self.send(text_data=json.dumps({"message": message}))
                    await self.send(text_data=html)
                except OSError:
                    pass  # Client may have disconnected
                # Clear the flag
                cache.delete(f"user_{user.id}_login_notification")
                logger.info(
                    "Consumers -> Login notification sent on connect for user: %s",
                    user.id,
                )

    async def system_notification(self, event):
        title = event.get("title", "Уведомление")
        message_text = event["message"]
        level = event.get("level", "info")
        timestamp = event.get("timestamp", timezone.now().isoformat())
        message = render_to_string(
            "core/partials/notifications.html",
            {
                "title": title,
                "message": message_text,
                "level": level,
                "timestamp": timestamp,
            },
        )
        logger.info("Consumers --> system_notification event: %s", event)
        try:
            await self.send(text_data=json.dumps({"message": message}))
        except OSError:
            pass  # Client may have disconnected

    async def user_joined(self, event):
        await self.send(text_data=event["text"])

    # def receive(self, text_data=None, bytes_data=None):
    #     # Called with either text_data or bytes_data for each frame
    #     # You can call:
    #     self.send(text_data="Hello world!")
    #     # Or, to send a binary frame:
    #     self.send(bytes_data="Hello world!")
    #     # Want to force-close the connection? Call:
    #     self.close()
    #     # Or add a custom WebSocket error code!
    #     self.close(code=4123)

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "group_name"):
            # cache.clear()
            logger.info(
                "Consumers --> disconnect group_name: %s, channel_name: %s",
                self.group_name,
                self.channel_name,
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
