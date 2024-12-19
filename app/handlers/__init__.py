# app/handlers/__init__.py

from .message_handlers import register_handlers as register_message_handlers

def register_all_handlers(dp):
    register_message_handlers(dp)
    # Если у вас есть другие обработчики, например, catalog_handlers, вы можете зарегистрировать их здесь
    # from .catalog_handlers import register_catalog_handlers
    # register_catalog_handlers(dp)
    # и так далее
