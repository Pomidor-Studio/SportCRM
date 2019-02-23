from .clients import Clients
from .hello import HelloCommand
from .schedule_clients import Schedule_clients

commands_list = [
    Clients(),
    HelloCommand(),
    Schedule_clients()
]
