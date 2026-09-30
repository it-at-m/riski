from datetime import date

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """ inclusive date range resolved from the users request."""

    start_date: date = Field(description= "first included calendar date in YYYY-MM-DD format")
    end_date: date = Field(description ="last included calendar date in YYYY-MM-DD formsat")