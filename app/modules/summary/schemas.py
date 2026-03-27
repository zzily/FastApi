from pydantic import BaseModel


class SummaryResponse(BaseModel):
    chart_data: dict
    financial_status: dict
    operational_status: dict
