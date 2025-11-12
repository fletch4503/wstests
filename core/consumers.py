# import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.template.loader import (
    # render_to_string,
    get_template,
)

# from django.utils import timezone

log = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Called on connection.
        self.user = self.scope["user"]
        if self.user.is_anonymous or not self.user.is_authenticated:
            await self.close()
        else:
            # self.group_name = f"user_{user.id}"
            self.group_name = "user-notifications"
            # self.group_name = f"user_{user.id}_notifications"
            # log.warning("User: %s, Group Name: %s", user, self.group_name)
            # Join room group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()  # To accept the connection
            # Check for login notification flag after accepting
            if cache.get(f"user_{self.user.id}_login_notification"):
                # Send login notification
                html = get_template("core/partials/notifications.html").render(
                    context={
                        "username": self.user.username,
                        "title": "Добро пожаловать!",
                        "message": f"{self.user.username} вошел в систему.",
                        "level": "info",
                    }
                )
                try:
                    # await self.send(text_data=json.dumps({"message": html}))
                    await self.send(text_data=html)
                except OSError:
                    pass  # Client may have disconnected
                # Clear the flag
                cache.delete(f"user_{self.user.id}_login_notification")
                log.warning(
                    "LOGIN User: %s, with Group Name: %s", self.user.id, self.group_name
                )

    async def system_notification(self, event):
        user = self.scope["user"]
        title_text = event["title"]
        message_text = event["message"]
        level = event["level"]
        timestamp = event["timestamp"]
        html = get_template("core/partials/notifications.html").render(
            context={
                "username": user.username,
                "title": title_text,
                "message": message_text,
                "level": level,
                "timestamp": timestamp,
            }
        )
        log.warning("EVENT: %s", event)
        try:
            await self.send(text_data=html)
            # await self.send(text_data=json.dumps({"message": message}))
        except OSError:
            pass  # Client may have disconnected

    async def user_joined(self, event):
        user = self.scope["user"]
        log.warning(
            "User %s, Sidned Up with EVENT: %s",
            user,
            event,
        )
        html = get_template("core/partials/notifications.html").render(
            context={
                "username": event["text"],
                "title": event["title"],
                "message": event["message"],
                "level": event["level"],
            }
        )
        await self.send(text_data=html)
        # await self.send(text_data=event["text"])

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
            log.warning(
                "DISCONNECT group_name: %s, channel_name: %s",
                self.group_name,
                self.channel_name,
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
