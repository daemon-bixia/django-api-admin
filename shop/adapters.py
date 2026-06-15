from allauth.headless.adapter import DefaultHeadlessAdapter
from dataclasses import asdict, dataclass
from datetime import datetime


class CustomHeadlessAdapter(DefaultHeadlessAdapter):
    def user_as_dataclass(self, user):
        user_dc = super().user_as_dataclass(user)
        UserDC = type(user_dc)

        @dataclass
        class CustomUserDC(UserDC):
            date_joined: datetime

        data = asdict(user_dc)
        return CustomUserDC(**data, date_joined=user.date_joined)
