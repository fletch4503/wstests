import json
import logging
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class NotificationConsumer(WebsocketConsumer):

    def connect(self):
        # Called on connection.
        # To accept the connection call:
        # cache.clear()
        user = self.scope["user"]
        if user.is_anonymous:
            self.close()
        else:
            # self.group_name = f"user_{user.id}"
            self.group_name = f"user_{user.id}_notifications"
            logger.info(
                "Consumers Connect --> Group Name: %s, Channel Name: %s",
                self.group_name,
                self.channel_name,
            )
            # Join room group
            async_to_sync(self.channel_layer.group_add)(
                self.group_name, self.channel_name
            )
            self.accept()  # To accept the connection
            # Check for login notification flag after accepting
            if cache.get(f"user_{user.id}_login_notification"):
                # Send login notification
                from django.template.loader import render_to_string
                from django.utils import timezone

                message = render_to_string(
                    "core/partials/notifications_partial.html",
                    {"username": user.username},
                )
                try:
                    self.send(text_data=json.dumps({"message": message}))
                except OSError:
                    pass  # Client may have disconnected
                # Clear the flag
                cache.delete(f"user_{user.id}_login_notification")
                logger.info(
                    "Consumers -> Login notification sent on connect for user: %s",
                    user.id,
                )

    def system_notification(self, event):
        message = event["message"]
        logger.info("Consumers --> system_notification event: %s", event)
        try:
            self.send(text_data=json.dumps({"message": message}))
        except OSError:
            pass  # Client may have disconnected

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

    def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "group_name"):
            # cache.clear()
            logger.info(
                "Consumers --> disconnect group_name: %s, channel_name: %s",
                self.group_name,
                self.channel_name,
            )
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )
