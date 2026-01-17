import os
import boto3
from boto3.dynamodb.conditions import Key

REGION = os.getenv("AWS_REGION", "ap-south-1")
TABLE = os.getenv("DDB_TABLE", "cloudops_metrics")

ddb = boto3.resource("dynamodb", region_name=REGION)
table = ddb.Table(TABLE)

def latest_metric(host_id: str):
    resp = table.query(
        KeyConditionExpression=Key("host_id").eq(host_id),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None
