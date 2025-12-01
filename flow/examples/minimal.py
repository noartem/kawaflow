from kawa import actor, event, NotSupportedEvent, Context
from kawa.cron import CronEvent


@actor(receivs=CronEvent.by("0 8 * * *"))
def MorningActor(ctx: Context, event):
    print("Good morning!")
