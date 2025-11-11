from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.core.cache import cache
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_notifications_on_signup(sender, instance, created, **kwargs):
    if created:
        cache.clear()
        # Отправляем уведомление через WebSocket
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.id}_notifications"
        channel_name = f"user_{instance.id}"
        event = {
            "type": "user_joined",
            # "type": "system_notification",
            "text": instance.username,
        }
        message = {
            "type": "system_notification",
            "level": "info",
            "title": "Добро пожаловать!",
            "message": f"Аккаунт {instance.email} успешно создан.",
            "timestamp": timezone.now().isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            group_name,
            message,
        )


# @receiver(user_logged_in)
def send_login_notification(sender, request, user, **kwargs):
    # Set a cache flag for login notification
    cache.set(
        f"user_{user.id}_login_notification", True, timeout=60
    )  # 60 seconds timeout
    logger.info("Signals -> Login notification flag set for user ID: %s", user.id)


user_logged_in.connect(send_login_notification)


# @receiver(user_logged_out)
def send_logout_notification(sender, request, user, **kwargs):
    # Отправляем уведомление о выходе через WebSocket
    cache.clear()
    channel_layer = get_channel_layer()
    group_name = f"user_{user.id}_notifications"
    channel_name = f"user_{user.id}"
    context = {
        "type": "system_notification",
        "level": "info",
        "title": "Выход из системы",
        "message": f"Пользователь {user.username} вышел из системы.",
        "timestamp": timezone.now().isoformat(),
    }
    logger.info("Выходит User: %s", user)
    async_to_sync(channel_layer.group_send)(
        group_name,
        context,
    )
    logger.info(
        "Signals -> LOGOUT notification sent to group: %s, Channel Name: %s",
        group_name,
        channel_name,
    )


user_logged_out.connect(send_logout_notification)
