#! pip install pyowm

from datetime import datetime, timedelta

from kawa.core import Actor, Event, Context, NotSupportedEvent
from kawa.cron import CronEvent
from kawa.email import SendEmailEvent


class GetDateWeatherInfoEvent(Event):
    def __init__(self, date):
        self.date = date


class DateWeatherInfoEvent(Event):
    def __init__(self, date: datetime, data: str):
        self.date = date
        self.data = data


def format_weather_info(data) -> str:
    return f"some weather info: {data}"


@Actor(
    receivs=(CronEvent.by("0 8 * * *"), DateWeatherInfoEvent),
    sends=(GetDateWeatherInfoEvent, SendEmailEvent, NotSupportedEvent),
)
def CreateDailyMessageActor(ctx: Context, event):
    """
    Create daily message
    """
    match event:
        case CronEvent():
            ctx.dispatch(GetDateWeatherInfoEvent(date=datetime.now()))
        case DateWeatherInfoEvent():
            ctx.dispatch(SendEmailEvent(message=format_weather_info(event.data)))


@Actor(
    receivs=(GetDateWeatherInfoEvent,),
    sends=(DateWeatherInfoEvent, CronEvent),
    max_instances=1,
    keep_instance=timedelta(minutes=1),
)
class WeatherActor:
    """
    Retrieve weather info.
    Using OpenWeather API
    """

    def __init__(self):
        # init weather api
        pass

    def __call__(self, ctx: Context, event):
        match event:
            case GetDateWeatherInfoEvent():
                # data = self.get_weather_info()
                data = f"some weather info: {event.date}"
                ctx.dispatch(DateWeatherInfoEvent(date=event.date, data=data))
