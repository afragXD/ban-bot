from VkBot.bot import VkBot

if __name__ == '__main__':
    from config import TOKEN, GROUP_ID, BANNED_PHRASES, BANNED_REPOST_GROUP

    bot = VkBot(token=TOKEN, group_id=GROUP_ID, banned_patterns=BANNED_PHRASES, banned_repost_groups=BANNED_REPOST_GROUP)
    bot.run()
