import boto3
import requests
import os
import time
import logging
from datetime import date, timedelta

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BudgetAgent")

# Config
API_URL = os.getenv("INGEST_URL", "http://localhost:8000/ingest")
# Default budget limit: $10.00
BUDGET_LIMIT = float(os.getenv("BUDGET_LIMIT", "10.0")) 

def get_current_cost():
    """Fetch Month-to-Date costs from AWS Cost Explorer"""
    client = boto3.client('ce', region_name='ap-south-1')
    
    today = date.today()
    first_day = today.replace(day=1)
    
    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': str(first_day),
                'End': str(today)  # End date is exclusive, so this gets up to yesterday
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        # Extract the dollar amount
        amount = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        return float(amount)
    except Exception as e:
        logger.error(f"Failed to fetch cost: {e}")
        return 0.0

def run():
    logger.info("Starting Budget Agent...")
    
    while True:
        cost = get_current_cost()
        logger.info(f"Current Month Cost: ${cost}")
        
        # Create a special metric payload for "Cost"
        payload = {
            "host_id": "aws-account-budget",  
            "env": "prod",
            "metrics": {
                "cost": cost,       
                "mem": 0,
                "disk": 0
            }
        }

        try:
            requests.post(API_URL, json=payload)
            logger.info("Sent cost metric to API.")
        except Exception as e:
            logger.error(f"Failed to send to API: {e}")
        time.sleep(86400)

if __name__ == "__main__":
    run()
