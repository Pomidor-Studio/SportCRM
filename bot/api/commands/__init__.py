from .clients import Clients
from .info import Information
from .hello import HelloCommand
from .schedule_clients import Schedule_clients

allowed_commands = [
    Clients(),
    HelloCommand(),
    Information(),
    Schedule_clients()
]
