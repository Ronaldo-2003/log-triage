from pydantic import BaseModel , Field
from typing import Optional,Dict,Any,List
from datetime import datetime

class IngestPayload(BaseModel):
    job_id : Optional[str] = Field(None , min_length=1 , max_length=64 , description="Optional job identifier (max 64 chars)")
    service : Optional[str] = Field(None , min_length=1 , max_length=64 , description="Optional service identifier(max 64 chars)")
    log_text : str = Field(... , max_length=5000 , description="Raw log text(max 5000 chars)")

class IngestManyPayload(BaseModel):
    logs : List[IngestPayload]

class IngestResponse(BaseModel):
    id : int
    status : str

class LogRecordOut(BaseModel):
    id : int
    log_text : str
    job_id : Optional[str] = None
    service : Optional[str] = None
    created_at : datetime
    # parsed and tags we will add later
    parsed : Optional[Dict[str,Any]] = None
    tags : Optional[list[str]] = None

    class Config:
        orm_mode= True

class PaginatedRecords(BaseModel):
    total : int
    limit : int
    offset : int
    page : int
    total_pages : int
    records : List[LogRecordOut]

class LogRecordList(BaseModel):
    records : List[LogRecordOut]

class PatchRecordPayload(BaseModel):
    job_id : Optional[str] = None
    service : Optional[str] = None
    log_text : Optional[str] = None
    manual_tags : Optional[List[str]] = None

    class Config:
        extra = "forbid"

