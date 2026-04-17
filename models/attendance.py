"""
TEAPS v5 - Attendance Record Model
Handles check-in/check-out tracking with location and QR validation
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Text, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class CheckType(str, enum.Enum):
    """Check-in/out types"""
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class AttendanceStatus(str, enum.Enum):
    """Attendance record status"""
    PENDING = "pending"  # Awaiting manager approval
    APPROVED = "approved"
    REJECTED = "rejected"
    LATE = "late"
    EARLY_LEAVE = "early_leave"
    ABSENT = "absent"


class AttendanceRecord(Base):
    """Daily attendance record with check-in/out times"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)  # Work date (not just check-in time)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    break_duration_minutes = Column(Integer, default=0)  # Total break time in minutes
    
    # Location data (optional, configurable) - now manual entry instead of QR
    check_in_location = Column(String(255))  # Manual location entry (optional)
    check_out_location = Column(String(255))
    
    # No QR code validation needed - text-based interaction
    
    # Working hours calculation
    scheduled_hours = Column(Float, default=8.0)  # Scheduled working hours
    actual_hours = Column(Float, default=0.0)  # Calculated from check-in/out
    
    # Status and notes
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PENDING)
    late_minutes = Column(Integer, default=0)
    early_leave_minutes = Column(Integer, default=0)
    manager_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("AttendanceRecordUser", back_populates="attendance_records")
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert attendance record to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.date().isoformat() if self.date else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'break_duration_minutes': self.break_duration_minutes,
            'scheduled_hours': self.scheduled_hours,
            'actual_hours': self.actual_hours,
            'status': self.status.value,
            'late_minutes': self.late_minutes,
            'early_leave_minutes': self.early_leave_minutes,
            'manager_notes': self.manager_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        # Only include location data for managers/admins (controlled by API)
        if include_sensitive:
            data['check_in_location'] = self.check_in_location
            data['check_out_location'] = self.check_out_location
            data['check_in_qr_code'] = self.check_in_qr_code
        
        return data
    
    def calculate_working_hours(self) -> float:
        """Calculate actual working hours from check-in/out times"""
        if not self.check_in_time or not self.check_out_time:
            return 0.0
        
        total_duration = (self.check_out_time - self.check_in_time).total_seconds() / 3600
        actual_hours = max(0, total_duration - (self.break_duration_minutes / 60))
        
        self.actual_hours = round(actual_hours, 2)
        return actual_hours
    
    def __repr__(self):
        return f"<AttendanceRecord {self.user_id} on {self.date.date()}>"


# Need to define this after User model is imported
def setup_relationships():
    """Setup bidirectional relationship between User and AttendanceRecord"""
    from .user import User
    AttendanceRecordUser = User
    AttendanceRecord.user = relationship("User", back_populates="attendance_records")
