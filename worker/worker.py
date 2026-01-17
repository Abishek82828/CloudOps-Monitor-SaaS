import os
import time
import logging
import boto3
import requests
from dynamo import latest_metric

# --- 1. Setup Logging ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudOpsWorker")

# --- Configuration ---
REGION = os.getenv("AWS_REGION", "ap-south-1")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")
ENV_TAG = os.getenv("ENV", "prod")

# Thresholds
CPU_T = float(os.getenv("CPU_THRESHOLD", "85"))
MEM_T = float(os.getenv("MEM_THRESHOLD", "85"))
DISK_T = float(os.getenv("DISK_THRESHOLD", "90"))
COOLDOWN = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "15"))

sns = boto3.client("sns", region_name=REGION)

last_alert_at = 0

# --- 2. Smart Host ID Detection (Matches Agent Logic) ---
def get_host_id():
    """
    Ensures Worker looks for the same ID that the Agent is writing.
    """
    if os.getenv("HOST_ID"):
        return os.getenv("HOST_ID")
    
    try:
        # Try to get real EC2 Instance ID
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
        import socket
        return socket.gethostname()

HOST_ID = get_host_id()

def should_alert(m):
    breaches = []
    # Convert Decimal to float just in case
    cpu = float(m["cpu"])
    mem = float(m["mem"])
    disk = float(m["disk"])

    if cpu >= CPU_T: breaches.append(f"CPU {cpu:.1f}% >= {CPU_T}%")
    if mem >= MEM_T: breaches.append(f"MEM {mem:.1f}% >= {MEM_T}%")
    if disk >= DISK_T: breaches.append(f"DISK {disk:.1f}% >= {DISK_T}%")
    return breaches

def send_alert(ts, breaches, m):
    # Use the env tag from the metric, or fallback to local config
    metric_env = m.get("env", ENV_TAG).upper()
    
    subject = f"[CloudOps][{metric_env}] Alert on {HOST_ID}"
    msg = (
        f"Environment: {metric_env}\n"
        f"Host: {HOST_ID}\n"
        f"Time: {ts}\n\n"
        f"Breaches:\n- " + "\n- ".join(breaches) + "\n\n"
        f"Current Metrics:\nCPU={m['cpu']}% | MEM={m['mem']}% | DISK={m['disk']}%\n"
    )
    
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=msg)
        logger.info(f"SNS Alert Sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send SNS alert: {e}")

def main():
    global last_alert_at
    logger.info(f"Worker starting. Watching Host: {HOST_ID}")

    while True:
        try:
            m = latest_metric(HOST_ID)
            
            if m:
                breaches = should_alert(m)
                now = int(time.time())
                
                if breaches:
                    # Check Cooldown
                    if (now - last_alert_at) >= COOLDOWN:
                        logger.warning(f"THRESHOLD BREACH: {breaches}")
                        if SNS_TOPIC_ARN:
                            send_alert(m["ts"], breaches, m)
                        last_alert_at = now
                    else:
                        logger.info(f"Breach active (CPU={m['cpu']}%), but in cooldown.")
                else:
                    logger.info(f"Status OK: CPU={m['cpu']}% MEM={m['mem']}% DISK={m['disk']}%")
            else:
                logger.warning(f"No metrics found yet for {HOST_ID}. Waiting for Agent...")
                
        except Exception as e:
            logger.error(f"Worker loop error: {e}")

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()