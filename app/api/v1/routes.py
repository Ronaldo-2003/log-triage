from fastapi import APIRouter , status , HTTPException , Query , Response
from app.api.v1.schemas import IngestPayload , IngestResponse , LogRecordOut , LogRecordList , IngestManyPayload , PaginatedRecords , PatchRecordPayload
from datetime import datetime
from typing import Optional , List
from math import ceil

router=APIRouter()

# temporary in-memory storage for logs
FAKE_DB : dict[int , dict] ={}
CURRENT_ID = 1

@router.post("/ingest" , response_model=IngestResponse , status_code=status.HTTP_201_CREATED)
def ingest(payload : IngestPayload):
    global CURRENT_ID
    record_id = CURRENT_ID
    CURRENT_ID+=1

    # just store raw log text in dictionary for now
    FAKE_DB[record_id]={
        "log_text" : payload.log_text,
        "job_id" : payload.job_id,
        "service" : payload.service,
        "created_at" : datetime.utcnow(),
    }

    return IngestResponse(id=record_id , status = "stored temporarily")

@router.post("/ingest/bulk" , response_model=List[IngestResponse] , status_code=status.HTTP_201_CREATED)
def ingest_bulk(payload : IngestManyPayload):
    global CURRENT_ID
    results : List[IngestResponse]=[]

    for entry in payload.logs:
        record_id=CURRENT_ID
        CURRENT_ID+=1

        FAKE_DB[record_id]={
            "log_text" : entry.log_text , 
            "job_id" : entry.job_id , 
            "service" : entry.service ,
            "created_at" : datetime.utcnow(),
        }

        results.append(IngestResponse(id=record_id , status="stored_temporarily"))
    
    return results

@router.get("/records" , response_model=PaginatedRecords)
def list_records(
    job_id:Optional[str]=None , 
    service:Optional[str]=None ,
    limit : int =Query(20 , ge=1 , le=200),
    offset : int =Query(0 , ge=0),
    sort : str =Query("created_at:desc")
    ):
    items : List[dict] = []

    for record_id , rec in FAKE_DB.items():

        # filter by job_id if provided
        if job_id is not None and rec.get("job_id") != job_id:
            continue

        # filter by service if provided
        if service is not None and rec.get("service") != service:
            continue

        items.append(
            {
                "id" : record_id,
                "log_text" : rec.get("log_text"),
                "job_id" : rec.get("job_id"),
                "service" : rec.get("service"),
                "created_at" : rec.get("created_at"),
                "parsed" : rec.get("parsed"),
                "tags" : rec.get("tags"),
            }
        )

    # parse and sanitize sort params
    # accept only whitelisted columns to prevent accidental injection/errors
    allowed_sort_fields = {"created_at"}
    try:
        col,order=sort.split(":")
    except ValueError:
        #fallback to default if client sends bad format
        col , order ="created_at" , "desc"

    col=col.strip()
    order=order.strip().lower()
    if col not in allowed_sort_fields:
        col="created_at"
    if order not in {"asc" , "desc"}:
        order = "desc"

    reverse=(order=="desc")

    # sort items
    def sort_key(r:dict):
        val = r.get(col)
        if isinstance(val,datetime):
            return val
        if isinstance(val,str):
            try:
                # parse ISO strings to datetime
                return datetime.fromisoformat(val)
            except:
                # unparseable strings should go to the beginning/end predictably
                return datetime.min
        return datetime.min
    
    items_sorted=sorted(items , key=sort_key , reverse=reverse)

    # compute total and slice for pagination
    total=len(items_sorted)
    page=items_sorted[offset:offset+limit]

    # compute page number and total pages
    if total==0:
        current_page=0
        total_pages=0
    else:
        current_page=(offset//limit)+1
        total_pages=ceil(total/limit)

    # return PaginatedRecords (Pydantic will validate and serialize)
    return PaginatedRecords(total=total , limit=limit , offset=offset , page=current_page , total_pages=total_pages , records=page)


@router.get("/records/{record_id}" , response_model=LogRecordOut)
def get_record(record_id : int):
    rec=FAKE_DB.get(record_id)
    if not rec:
        raise HTTPException(status_code=404 , detail= "record not found")
    
    response = {
        "id" : record_id , 
        "log_text" : rec.get("log_text" , ""),
        "job_id" : rec.get("job_id"),
        "service" : rec.get("service"),
        "created_at" : rec.get("created_at"),
        # parsed/tags are None for now; they will be filled after parsing step
        "parsed" : rec.get("parsed") ,
        "tags" : rec.get("tags")
    }

    return response

@router.patch("/records/{record_id}" , response_model=LogRecordOut)
def patch_record(record_id : int, payload : PatchRecordPayload):
    # locate record
    rec = FAKE_DB.get(record_id)
    if not rec:
        raise HTTPException(status_code=404 , detail="record not found")
    
    # update record fields only if provided
    if payload.job_id is not None:
        rec["job_id"]=payload.job_id
    if payload.service is not None:
        rec["service"]=payload.service
    if payload.log_text is not None:
        rec["log_text"]=payload.log_text
    if payload.manual_tags is not None:
        rec["manual_tags"]=payload.manual_tags

    # set audit timestamp
    rec["updated_at"]=datetime.utcnow()

    # return updated record in expected format
    return{
        "id" : record_id,
        "log_text" : rec.get("log_text" ,),
        "job_id" : rec.get("job_id") ,
        "service" : rec.get("service"),
        "created_at" : rec.get("created_at"),
        "parsed" : rec.get("parsed"),
        "tags" : rec.get("manual_tags") or rec.get("tags") ,
    }

@router.delete("/records/{record_id}" , status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id : int):
    # soft deleting by setting deleted_at
    rec=FAKE_DB.get(record_id)
    if not rec:
        raise HTTPException(status_code=404 , detail="record not found")
    
    # if already deleted , treat as idempotent - delete again returns 204
    if rec.get("deleted_at") is not None:
        return Response(status_code=204)
    
    rec["deleted_at"] = datetime.utcnow()
    return Response(status_code=204)