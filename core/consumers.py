import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import async_to_sync


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
            print(
                "Consumers Connect --> Group Name:",
                self.group_name,
                " Channel Name:",
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
                self.send(text_data=json.dumps({"message": message}))
                # Clear the flag
                cache.delete(f"user_{user.id}_login_notification")
                print(
                    "Consumers -> Login notification sent on connect for user:", user.id
                )

    def system_notification(self, event):
        message = event["message"]
        print("Consumers --> system_notification event:", event)
        self.send(text_data=json.dumps({"message": message}))

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
            print(
                "Consumers --> disconnect group_name: ",
                self.group_name,
                "channel_name: ",
                self.channel_name,
            )
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )
