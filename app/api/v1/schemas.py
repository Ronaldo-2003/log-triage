from pydantic import BaseModel , Field , model_validator
from typing import Optional,Dict,Any,List,Annotated
from datetime import datetime

class IngestPayload(BaseModel):
    job_id : Optional[str] = Field(None , min_length=1 , max_length=64 , description="Optional job identifier (max 64 chars)")
    service : Optional[str] = Field(None , min_length=1 , max_length=64 , description="Optional service identifier(max 64 chars)")
    log_text : str = Field(... , max_length=5000 , description="Raw log text(max 5000 chars)")

    model_config={"extra" : "forbid"}

class IngestManyPayload(BaseModel):
    logs : Annotated[
                        List[IngestPayload],
                        Field(... , min_items=1 , max_items=100 ,description="List of logs(1...100)")
                    ]

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

    model_config = {"from_attributes" : True , "extra" : "forbid"} 

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
    job_id : Optional[str] = Field(None , min_length=1 , max_length=64)
    service : Optional[str] = Field(None , min_length=1 , max_length=64)
    log_text : Optional[str] = Field(None , max_length=5000)
    manual_tags : Optional[Annotated[List[str] , Field(max_items=20)]] = None

    # model validator to enforce per tag constraints
    @model_validator(mode="after")
    def validate_manual_tags(self):
        tags=self.manual_tags

        if tags is None:
            return self
        if not isinstance(tags , list):
            raise ValueError("manual_tags must be a list of strings")
        if len(tags) > 20:
            raise ValueError("manual_tags can have at most 20 items")
        
        for tag in tags:
            if not isinstance(tag , str):
                raise ValueError("each manual_tag must be a string")
            if len(tag.strip())==0:
                raise ValueError("manual_tag cannot be empty")
            if len(tag) > 64:
                raise ValueError("each manual_tag must be at most 64 characters")
        
        return self
        

    model_config = {"extra" : "forbid"}

