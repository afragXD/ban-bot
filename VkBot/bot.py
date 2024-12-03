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
            text = message["text"].lower()
            conversation_message_id = message["conversation_message_id"]

            # Проверяем текст сообщения на наличие запрещённых паттернов
            if any(pattern.search(text) for pattern in self.banned_patterns):
                self.delete_message(peer_id, conversation_message_id)
                return

            # Проверяем репосты из запрещённых групп
            if "attachments" in message:
                for attachment in message["attachments"]:
                    if attachment["type"] == "wall":
                        repost = attachment["wall"]
                        if "from_id" in repost and str(repost["from_id"]) in self.banned_repost_groups:
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