import datetime
from enum import Enum

from django.db import models


class OrcaState(models.Model):
    device_ip = models.CharField(max_length=64, primary_key=True)
    state = models.CharField(max_length=64)
    last_updated_time = models.DateTimeField(null=True)

    objects = models.Manager()

    @staticmethod
    def update_state(device_ip, state):
        state_obj = OrcaState.objects.get(device_ip=device_ip)
        state_obj.state = str(state)
        state_obj.last_updated_time = datetime.datetime.now(datetime.timezone.utc)
        state_obj.save()


class State(Enum):
    AVAILABLE = "Available"
    DISCOVERY_IN_PROGRESS = "Discovery in progress"
    FEATURE_DISCOVERY_IN_PROGRESS = "Feature discovery in progress"
    SCHEDULED_DISCOVERY_IN_PROGRESS = "Scheduled discovery in progress"
    CONFIG_IN_PROGRESS = "Config in progress"
    INSTALL_IN_PROGRESS = "Install in progress"

    @staticmethod
    def get_enum_from_str(name: str):
        return State[name] if name in State.__members__ else None

    def __str__(self) -> str:
        return self.name