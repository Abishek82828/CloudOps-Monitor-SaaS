import time
import logging
from decimal import Decimal  # <--- NEW IMPORT
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError
from dynamo import put_metric

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudOpsAPI")

app = FastAPI(title="CloudOps Ingest API")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

class Metrics(BaseModel):
    cpu: float = Field(..., ge=0, le=100)
    mem: float = Field(..., ge=0, le=100)
    disk: float = Field(..., ge=0, le=100)

class IngestPayload(BaseModel):
    host_id: str
    env: str = "prod"
    ts: int | None = None
    metrics: Metrics

@app.get("/health")
def health():
    return {"ok": True, "status": "healthy"}

@app.post("/ingest")
def ingest(p: IngestPayload):
    ts = p.ts or int(time.time())

    # --- THE FIX: Convert floats to Decimal ---
    item = {
        "host_id": p.host_id,
        "ts": str(ts),
        "env": p.env,
        "cpu": Decimal(str(p.metrics.cpu)),
        "mem": Decimal(str(p.metrics.mem)),
        "disk": Decimal(str(p.metrics.disk)),
    }

    try:
        put_metric(item)
        logger.info(f"Success: Ingested metrics for host={p.host_id}, env={p.env}")
        return {
            "stored": True, 
            "host_id": p.host_id, 
            "ts": ts,
            "message": "Metric persisted successfully"
        }
    
    except ClientError as e:
        error_msg = e.response['Error']['Message']
        logger.error(f"DynamoDB Error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    except Exception as e:
        logger.error(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
