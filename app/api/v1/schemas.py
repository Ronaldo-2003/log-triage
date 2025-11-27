from pydantic import BaseModel
from typing import Optional,Dict,Any,List
from datetime import datetime

class IngestPayload(BaseModel):
    job_id : Optional[str] =None
    service : Optional[str] = None
    log_text : str

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

