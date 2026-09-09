from datetime import datetime, date, time, timedelta
from typing import Literal, Annotated
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field


class TimeRangeError(Exception):
    pass
# wenn eine Zeitangabe syntaktisch gültig ist, aber keinen sinn ergibt 


class RelativePeriod(BaseModel):            # fester Kalenderblock relativ zu heute, z.B. "letzter Monat"

    kind: Literal["relative"] = "relative"
    unit: Literal["day", "week", "month", "quarter", "year"]
    offset: int

def resolve_relative(spec: RelativePeriod, now: datetime) -> tuple[datetime, datetime, str]:
    if spec.unit == "month":
        anchor = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None,) #Auf 1. des Monats setzten 
        start = anchor + relativedelta(months=spec.offset)
        end = start + relativedelta(months=1)
        label = start.strftime("%B %Y")
        return start, end, label
    
    # Gleiches Prinzip wie oben bei "month", nur Anker = 1. Januar.

    if spec.unit == "year":
        anchor = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        start = anchor + relativedelta(years=spec.offset)
        end = start + relativedelta(years=1)
        label = start.strftime("%Y")
        return start, end, label
           
    raise NotImplementedError(f"unit {spec.unit} noch nicht implementiert")


class ExplicitPeriod(BaseModel):                    # Wenn nutzer Nutzer Start-/Enddatum explizit nennt 
    kind: Literal["explicit"] = "explicit"
    start: date
    end: date


def resolve_explicit(spec: ExplicitPeriod) -> tuple[datetime, datetime, str]:
    if spec.start > spec.end:
        raise TimeRangeError("Startdatum liegt nach dem Enddatum.")
    start = datetime.combine(spec.start, time.min)
    end = datetime.combine(spec.end + timedelta(days=1), time.min)
    label = f"{spec.start:%d.%m.%Y}–{spec.end:%d.%m.%Y}"    
    return start, end, label


class DurationPeriod(BaseModel):                            #ab jetzt zurückgerechnet, z.B. "letzte 3 Monate"
    kind: Literal["duration"] = "duration"
    amount: int
    unit: Literal["day", "week", "month", "year"]


def resolve_duration(spec: DurationPeriod, now: datetime) -> tuple[datetime, datetime, str]:
    if spec.amount <= 0:
        raise TimeRangeError("Die Anzahl muss positiv sein.")
    end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    start = end - relativedelta(**{f"{spec.unit}s": spec.amount})
    label = f"die letzten {spec.amount} {spec.unit}(e)"
    return start, end, label


TimeSpec = Annotated[                                               #kind Feld im LLM-Output wird angeschaut --> damit direkt in richtige Klasse geparsd wird 
    RelativePeriod | ExplicitPeriod | DurationPeriod,
    Field(discriminator="kind"),
]


def resolve(spec: TimeSpec, now: datetime) -> tuple[datetime, datetime, str]:
    now = now.replace(tzinfo=None)                  # DB-Spalte hat keine Zeitzone, führt sonst zu Problemen bei späterer SQL-Query
    match spec:
        case RelativePeriod():                       # ist spec eine Instanz von RelativePeriod?
            return resolve_relative(spec, now)
        case ExplicitPeriod():                       # ist spec eine Instanz von ExplicitPeriod?
            return resolve_explicit(spec)
        case DurationPeriod():                       # ist spec eine Instanz von DurationPeriod?
            return resolve_duration(spec, now)       