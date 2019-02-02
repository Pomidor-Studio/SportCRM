from django.apps import AppConfig


class BotConfig(AppConfig):
    name = 'bot'

class SignalsConfig(AppConfig):
    name = 'bot.api.signals'

    def ready(self):
        import bot.api.signals.handlers
