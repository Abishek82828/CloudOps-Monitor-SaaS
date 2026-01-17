# CloudOps SaaS Monitoring Platform

**A real-time health and cost monitoring platform for AWS infrastructure.**

---

##  What is this?

CloudOps SaaS Monitoring Platform is a custom-built monitoring system designed to track **system health and AWS costs in real time**.

It monitors:
- CPU usage
- RAM usage
- Disk usage
- AWS billing data

When resource usage spikes or costs cross a defined threshold, the system sends an **instant SMS alert** to avoid surprises.

This project was built as a **lightweight, microservices-based alternative** to tools like Datadog, designed to run **practically free on the AWS Free Tier**.

---

## Architecture

The platform is fully containerized using Docker and follows a **microservices architecture**:

- **Agent**  
  Collects server metrics (CPU, memory, disk) every 15 seconds.

- **API Service**  
  Receives metrics and stores them in **AWS DynamoDB**.

- **Worker Service**  
  Continuously checks metrics and triggers alerts using **AWS SNS**.

- **Budget Watcher**  
  Checks AWS Cost Explorer daily to detect unexpected billing increases.

- **Dashboard**  
  A real-time **Streamlit dashboard** to visualize system health and cost trends.

---

## Tech Stack

### Cloud
- AWS EC2
- AWS DynamoDB
- AWS SNS
- AWS Cost Explorer
- AWS IAM

### Backend & UI
- Python
- FastAPI
- Boto3
- Streamlit

### DevOps & System
- Docker
- Docker Compose
- Linux

---

## ⚙️ How to Run Locally

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Abishek82828/CloudOps-Monitor-SaaS.git
cd CloudOps-Monitor-SaaS
```

### 2️⃣ Configure Environment Variables
Edit the `.env` file and add:
- AWS Region
- SNS Topic ARN
- Any required AWS credentials (IAM role preferred)

---

### 3️⃣ Build and Run the Services
```bash
docker compose up --build -d
```

---

### 4️⃣ Access the Dashboard
Open your browser and visit:
```
http://localhost:8501
```

---

## Key Learnings

- Cloud cost visibility should be part of architecture, not an afterthought
- Monitoring and alerting are as important as application logic
- Small AWS configuration mistakes can have large cost impact
- Building from real mistakes leads to better system design

---

## 🔗 Links

- **GitHub:** https://github.com/Abishek82828
- **LinkedIn:** https://www.linkedin.com/in/abishek202/

---

## 📌 Note

This project is a learning-focused implementation inspired by real-world AWS cost incidents.  
It is designed to be simple, extendable, and production-aware.
