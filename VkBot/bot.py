import time
import re
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


class VkBot:
    def __init__(self, token, group_id, banned_patterns, banned_repost_groups):
        """
        Инициализация бота.

        :param token: Токен доступа к API ВКонтакте.
        :param group_id: ID группы ВКонтакте.
        :param banned_patterns: Список запрещённых паттернов (регулярных выражений) для модерации сообщений.
        """
        self.token = token
        self.group_id = group_id
        self.banned_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in banned_patterns]
        self.banned_repost_groups = [f"-{group_id}" for group_id in banned_repost_groups]

        # Инициализация сессии VK API
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()

        # Инициализация LongPoll
        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)

        # Хранение времени последнего стикера для каждого пользователя
        self.last_sticker_time = {}

    def delete_message(self, peer_id, message_id):
        """
        Удаление сообщения.

        :param peer_id: ID беседы или пользователя.
        :param message_id: ID сообщения в беседе.
        """
        try:
            self.vk.messages.delete(peer_id=peer_id, conversation_message_ids=message_id, delete_for_all=True)
            print(f"Удалено сообщение с ID {message_id} в беседе {peer_id}")
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка при удалении сообщения: {e}")

    def handle_event(self, event):
        """
        Обработка одного события.

        :param event: Событие из LongPoll.
        """
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            peer_id = message["peer_id"]
            from_id = message["from_id"]  # ID отправителя
            conversation_message_id = message["conversation_message_id"]

            # Проверяем, если сообщение содержит стикер
            if "attachments" in message:
                for attachment in message["attachments"]:
                    if attachment["type"] == "sticker":
                        # Получаем текущее время
                        current_time = time.time()

                        # Проверяем кулдаун на стикеры для пользователя
                        last_time = self.last_sticker_time.get(from_id, 0)
                        if current_time - last_time < 60:
                            self.delete_message(peer_id, conversation_message_id)
                            return

                        # Обновляем время отправки стикера для пользователя
                        self.last_sticker_time[from_id] = current_time
                        return

            # Проверяем текст сообщения на наличие запрещённых паттернов
            text = message["text"].lower()
            if any(pattern.search(text) for pattern in self.banned_patterns):
                self.delete_message(peer_id, conversation_message_id)
                return

    def run(self):
        """
        Запуск бота.
        """
        print("Бот запущен и работает...")
        try:
            for event in self.longpoll.listen():
                self.handle_event(event)
        except Exception as e:
            print(f"Ошибка в работе бота: {e}")
