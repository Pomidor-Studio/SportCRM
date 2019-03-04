from .clients import Clients
from .info import Information
from .hello import HelloCommand
from .schedule_clients import ScheduleClients

allowed_commands = [
    Clients(),
    HelloCommand(),
    Information(),
    ScheduleClients()
]
