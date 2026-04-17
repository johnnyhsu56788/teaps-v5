"""
TEAPS v5 - FastAPI Web Application
Main application entry point with RESTful API endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import uvicorn

# Import TEAPS components
from utils.database import get_session, sanitize_log_data
from utils.qrcode_auth import get_qr_auth, validate_scanned_qr
from handlers.bot_handlers import AttendanceHandler, PayrollHandler, AdminHandler

app = FastAPI(
    title="TEAPS v5 - Attendance & Payroll System",
    description=" bilingual Telegram-based attendance and payroll management system",
    version="5.0.0"
)

# Initialize QR auth
qr_auth = get_qr_auth()


# Dependency injection for database sessions
def get_db():
    """Get database session dependency"""
    db = next(get_session())
    try:
        yield db
    finally:
        db.close()


# Middleware for logging (production would use proper logging)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests"""
    print(f"[API] {request.method} {request.url.path}")
    response = await call_next(request)
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "version": "5.0.0"}


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login")
async def login(credentials: dict, db: Session = Depends(get_db)):
    """
    User login endpoint
    
    Request body:
        - username: Employee ID or email
        - password: Plain text password
    
    Returns:
        JWT token and user info
    """
    from models.user import User
    
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Missing username or password"
        )
    
    # Find user by employee_id or email
    user = db.query(User).filter(
        (User.employee_id == username) | (User.email == username)
    ).first()
    
    if not user or not user.check_password(password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # In production, generate JWT token here
    return {
        "access_token": f"mock_jwt_token_{user.id}",
        "token_type": "bearer",
        "user": user.to_dict(include_sensitive=False)
    }


@app.post("/api/auth/logout")
async def logout():
    """User logout endpoint"""
    return {"message": "Logged out successfully"}


# ==================== Attendance Endpoints ====================

@app.get("/api/attendance/my-status")
async def get_my_attendance_status(db: Session = Depends(get_db)):
    """Get current user's today's attendance status"""
    from models.attendance import AttendanceRecord, AttendanceStatus
    
    # Get user from JWT token (simplified - in production use OAuth)
    user_id = 1  # TODO: Extract from JWT
    
    today = __import__('datetime').date.today().isoformat()
    
    record = db.query(AttendanceRecord).filter_by(
        user_id=user_id,
        date=today
    ).first()
    
    if not record:
        return {
            "has_checked_in": False,
            "message": "您尚未簽到，請使用 Telegram Bot 進行簽到",
            "status": "pending"
        }
    
    return {
        "has_checked_in": True,
        "check_in_time": record.check_in_time.isoformat() if record.check_in_time else None,
        "check_out_time": record.check_out_time.isoformat() if record.check_out_time else None,
        "status": record.status.value,
        "actual_hours": record.actual_hours
    }


@app.post("/api/attendance/checkin")
async def check_in(
    data: dict,
    db: Session = Depends(get_db)
):
    """
    Process manual check-in request (text-based, no QR code)
    
    Request body:
        - location: Optional location string (e.g., "Office Floor 5")
    
    Returns:
        Created attendance record with PENDING status
    """
    from models.attendance import AttendanceRecord, AttendanceStatus
    
    # Get user_id from JWT token or authentication (simplified)
    user_id = data.get("user_id", 1)  # TODO: Extract from JWT properly
    
    location = data.get("location")
    
    with get_session() as db_session:
        today = __import__('datetime').date.today().isoformat()
        
        # Check if already has a record for today
        existing_record = db_session.query(AttendanceRecord).filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if existing_record and existing_record.check_in_time:
            raise HTTPException(
                status_code=409,
                detail="您今天已經簽到了，請等待上級核准"
            )
        
        # Create new attendance record with PENDING status
        new_record = AttendanceRecord(
            user_id=user_id,
            date=today,
            check_in_time=__import__('datetime').datetime.now(),
            check_in_location=location or "Manual Entry",
            status=AttendanceStatus.PENDING  # Requires manager approval
        )
        
        db_session.add(new_record)
        db_session.commit()
    
    return {
        "success": True,
        "message": "簽到申請已提交，請等待上級核准",
        "record_id": new_record.id,
        "check_in_time": new_record.check_in_time.isoformat(),
        "status": "pending_approval"
    }


@app.post("/api/attendance/checkout")
async def check_out(
    data: dict,
    db: Session = Depends(get_db)
):
    """Process manual checkout request (text-based, no QR code)"""
    from models.attendance import AttendanceRecord
    
    user_id = data.get("user_id", 1)
    
    with get_session() as db_session:
        today = __import__('datetime').date.today().isoformat()
        
        record = db_session.query(AttendanceRecord).filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if not record or not record.check_in_time:
            raise HTTPException(
                status_code=404,
                detail="您今天尚未簽到，無法簽退"
            )
        
        # Only allow checkout for approved records
        if record.status != AttendanceStatus.APPROVED:
            raise HTTPException(
                status_code=403,
                detail="您的簽到記錄尚未核准，無法簽退"
            )
        
        record.check_out_time = __import__('datetime').datetime.now()
        record.calculate_working_hours()
        
        db_session.commit()
    
    return {
        "success": True,
        "message": "簽退成功",
        "record_id": record.id,
        "check_out_time": record.check_out_time.isoformat(),
        "working_hours": record.actual_hours
    }


@app.post("/api/admin/approve-attendance")
async def approve_attendance(
    record_id: int,
    approved: bool = True,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Approve or reject an attendance record (admin only)"""
    from models.attendance import AttendanceRecord, AttendanceStatus
    
    # TODO: Add admin authorization check
    
    record = db.query(AttendanceRecord).filter_by(id=record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="記錄不存在")
    
    new_status = AttendanceStatus.APPROVED if approved else AttendanceStatus.REJECTED
    record.status = new_status
    
    if notes:
        record.manager_notes = notes
    
    db.commit()
    
    user_name = record.user.name_tc if record.user else "Unknown"
    status_text = "已核准" if approved else "已拒絕"
    
    return {
        "success": True,
        "message": f"{user_name} 的出勤記錄已{status_text}",
        "record_id": record_id,
        "new_status": new_status.value
    }


@app.get("/api/admin/pending-records")
async def get_pending_records(db: Session = Depends(get_db)):
    """Get all pending attendance records for today (admin only)"""
    from models.attendance import AttendanceRecord
    
    # TODO: Add admin authorization check
    
    today = __import__('datetime').date.today().isoformat()
    
    records = db.query(AttendanceRecord).filter_by(
        date=today,
        status=AttendanceStatus.PENDING
    ).all()
    
    return {
        "pending_records": [
            record.to_dict(include_sensitive=False) 
            for record in records
        ],
        "total": len(records)
    }


# ==================== Payroll Endpoints ====================

@app.get("/api/payroll/my-payroll")
async def get_my_payroll(month: Optional[int] = None, db: Session = Depends(get_db)):
    """Get current user's payroll for specified month"""
    from models.payroll import PayrollRecord
    
    user_id = 1  # TODO: Extract from JWT
    
    if not month:
        # Default to current month
        from datetime import datetime
        now = datetime.now()
        month = now.month
        year = now.year
    else:
        year = datetime.now().year
    
    record = db.query(PayrollRecord).filter_by(
        user_id=user_id,
        period_start=f"{year}-{month:02d}-01",
        period_end=f"{year}-{month:02d}-28"  # Simplified end date
    ).first()
    
    if not record:
        return {
            "message": f"No payroll record found for {year}-{month:02d}",
            "status": "pending_calculation"
        }
    
    return {
        "payroll": record.to_dict(include_sensitive=False),
        "period": f"{year}-{month:02d}"
    }


@app.get("/api/payroll/summary")
async def get_payroll_summary(
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get payroll summary for all employees (admin only)"""
    from models.payroll import PayrollRecord
    
    # TODO: Add admin authorization check
    
    if not month:
        from datetime import datetime
        now = datetime.now()
        month = now.month
        year = now.year
    else:
        year = datetime.now().year
    
    records = db.query(PayrollRecord).filter(
        PayrollRecord.period_start.like(f"{year}-{month:02d}%")
    ).all()
    
    total_gross = sum(r.gross_pay for r in records)
    total_net = sum(r.net_pay for r in records)
    
    return {
        "period": f"{year}-{month:02d}",
        "total_employees": len(records),
        "summary": {
            "total_gross_pay": round(total_gross, 2),
            "total_net_pay": round(total_net, 2)
        },
        "records": [r.to_dict(include_sensitive=True) for r in records]
    }


# ==================== Admin Endpoints ====================

@app.post("/api/admin/approve-attendance")
async def approve_attendance(
    record_id: int,
    approved: bool = True,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Approve or reject an attendance record (admin only)"""
    from models.attendance import AttendanceRecord, AttendanceStatus
    
    # TODO: Add admin authorization check
    
    record = db.query(AttendanceRecord).filter_by(id=record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    new_status = AttendanceStatus.APPROVED if approved else AttendanceStatus.REJECTED
    record.status = new_status
    record.manager_notes = notes
    
    db.commit()
    
    user_name = record.user.name_tc if record.user else "Unknown"
    status_text = "已核准" if approved else "已拒絕"
    
    return {
        "success": True,
        "message": f"{user_name} 的出勤記錄已{status_text}",
        "record_id": record_id,
        "new_status": new_status.value
    }


@app.get("/api/admin/employees")
async def get_employees(department_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get list of all employees (admin only)"""
    from models.user import User
    
    query = db.query(User).filter_by(is_active=True)
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    users = query.all()
    
    return {
        "employees": [user.to_dict(include_sensitive=False) for user in users],
        "total": len(users)
    }


# ==================== Web Dashboard Routes ====================

@app.get("/")
async def serve_dashboard():
    """Serve the Vue.js dashboard (in production would serve static files)"""
    return {
        "message": "TEAPS v5 Dashboard",
        "docs": "/docs",
        "health": "/health"
    }


# Mount static files and templates (in production)
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
