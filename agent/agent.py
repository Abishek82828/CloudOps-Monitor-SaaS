import os
import time
import logging
import psutil
import requests

# --- 1. Setup Logging ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudOpsAgent")

# --- Configuration ---
INGEST_URL = os.getenv("INGEST_URL", "http://localhost:8000/ingest")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "15"))
ENV_TAG = os.getenv("ENV", "prod") # New: Matches your API update

# --- 2. Smart Host ID Detection ---
def get_host_id():
    """
    Priority:
    1. ENV Variable (Manual Override)
    2. AWS EC2 Metadata (Real Instance ID)
    3. Hostname (Fallback)
    """
    if os.getenv("HOST_ID"):
        return os.getenv("HOST_ID")
    
    try:
        # Try to get real EC2 Instance ID (timeout fast if not on EC2)
        token = requests.put(
            "http://169.254.169.254/latest/api/token", 
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, 
            timeout=1
        ).text
        instance_id = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id", 
            headers={"X-aws-ec2-metadata-token": token},
            timeout=1
        ).text
        logger.info(f"Detected EC2 Instance ID: {instance_id}")
        return instance_id
    except:
        # Fallback to local hostname
        import socket
        return socket.gethostname()

HOST_ID = get_host_id()

def collect():
    """Gather system metrics"""
    try:
        # cpu_percent(interval=None) is non-blocking if called repeatedly, 
        # but for simple agents, interval=1 is fine (blocks for 1s).
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        return {"cpu": cpu, "mem": mem, "disk": disk}
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return None

def main():
    logger.info(f"Agent starting for Host: {HOST_ID} | Env: {ENV_TAG}")
    logger.info(f"Targeting API: {INGEST_URL}")

    while True:
        metrics = collect()
        if metrics:
            payload = {
                "host_id": HOST_ID, 
                "env": ENV_TAG,
                "metrics": metrics
            }
            
            try:
                r = requests.post(INGEST_URL, json=payload, timeout=5)
                if r.status_code == 200:
                    logger.info(f"Sent metrics: CPU={metrics['cpu']}% MEM={metrics['mem']}% DISK={metrics['disk']}%")
                else:
                    logger.warning(f"Failed to send. Status: {r.status_code} | Response: {r.text}")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection Failed: Could not reach API at {INGEST_URL}. Is it running?")
            except Exception as e:
                logger.error(f"Unexpected error sending data: {e}")
        
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()