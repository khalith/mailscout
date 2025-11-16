# 📧 MailScout – Email Verification SaaS

MailScout is a fully asynchronous, globally scalable email verification system built using:

- FastAPI (backend)
- Async Workers (DNS, MX, SMTP checks)
- Redis Queue (Upstash)
- PostgreSQL (Neon)
- React + Tailwind (frontend)
- Fly.io (global deployment)
- Autoscaler (dynamic worker scaling)

---

## 🚀 Features

✓ CSV upload with lakhs of emails  
✓ Email syntax validation  
✓ DNS / MX lookup  
✓ SMTP handshake without sending emails  
✓ Disposable detection  
✓ Role-based detection  
✓ Catch-all detection  
✓ Deliverability scoring (0–100)  
✓ Real-time dashboard  
✓ Worker autoscaling (Fly.io + Redis LLEN)

---

## 🔧 Technology Stack

### Backend (FastAPI)
Located in `backend/`  
Responsible for:
- CSV parsing
- Job chunking
- Queue push to Redis
- Data persistence (PostgreSQL)

### Worker (Async Python)
Located in `worker/`  
Responsible for:
- DNS/MX queries
- SMTP handshake  
- Scoring engine  
- Batch DB commits

### Frontend (React + Tailwind)
Located in `frontend/`  
Responsible for:
- Upload UI  
- CSV preview  
- Dashboard  
- Results table  

### Autoscaler
Located in `autoscaler/`  
Scales workers based on Redis queue length.

---

## ▶️ Running Locally (docker-compose)

```bash
docker-compose up --build
