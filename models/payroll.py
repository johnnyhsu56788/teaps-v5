"""
TEAPS v5 - Payroll Record Model
Handles salary calculation with overtime, deductions, and bonuses
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Text, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class PayrollPeriod(str, enum.Enum):
    """Payroll period types"""
    MONTHLY = "monthly"
    BI_WEEKLY = "bi_weekly"
    WEEKLY = "weekly"


class PaymentStatus(str, enum.Enum):
    """Payment status tracking"""
    PENDING = "pending"  # Awaiting approval
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    HOLD = "hold"


class PayrollRecord(Base):
    """Monthly payroll record with detailed breakdown"""
    __tablename__ = 'payroll_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)  # Period start date
    period_end = Column(DateTime, nullable=False)  # Period end date
    
    # Base salary components
    base_salary = Column(Float, nullable=False)  # Basic monthly salary
    attendance_days = Column(Integer, default=0)  # Actual working days
    scheduled_days = Column(Integer, default=0)  # Scheduled working days in period
    
    # Earnings
    overtime_hours = Column(Float, default=0.0)
    overtime_rate = Column(Float, default=1.5)  # Overtime multiplier (1.5x, 2x, etc.)
    overtime_pay = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    allowance = Column(Float, default=0.0)  # Transport, meal allowances
    
    # Deductions
    deduction_absent = Column(Float, default=0.0)  # Absence deduction
    deduction_late = Column(Float, default=0.0)  # Late arrival deduction
    deduction_other = Column(Float, default=0.0)  # Other deductions (loans, etc.)
    
    # Tax and social security (configurable by country/region)
    tax_deduction = Column(Float, default=0.0)
    social_security = Column(Float, default=0.0)
    
    # Final calculations
    gross_pay = Column(Float, default=0.0)  # Total before deductions
    net_pay = Column(Float, default=0.0)  # Take-home pay after all deductions
    
    # Status and approval
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Notes and comments
    notes = Column(Text)
    manager_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("PayrollRecordUser", back_populates="payroll_records")
    approver = relationship("User", foreign_keys=[approved_by])
    
    def calculate_gross_pay(self) -> float:
        """Calculate gross pay from all earnings components"""
        self.gross_pay = (
            self.base_salary + 
            self.overtime_pay + 
            self.bonus + 
            self.allowance
        )
        return round(self.gross_pay, 2)
    
    def calculate_net_pay(self) -> float:
        """Calculate net pay after all deductions"""
        total_deductions = (
            self.deduction_absent +
            self.deduction_late +
            self.deduction_other +
            self.tax_deduction +
            self.social_security
        )
        
        self.net_pay = max(0, self.gross_pay - total_deductions)
        return round(self.net_pay, 2)
    
    def calculate_all(self):
        """Calculate all payroll components in sequence"""
        self.calculate_gross_pay()
        self.calculate_net_pay()
        return {
            'gross_pay': self.gross_pay,
            'net_pay': self.net_pay,
            'total_deductions': sum([
                self.deduction_absent,
                self.deduction_late,
                self.deduction_other,
                self.tax_deduction,
                self.social_security
            ])
        }
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert payroll record to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'period_start': self.period_start.date().isoformat() if self.period_start else None,
            'period_end': self.period_end.date().isoformat() if self.period_end else None,
            'base_salary': self.base_salary,
            'attendance_days': self.attendance_days,
            'scheduled_days': self.scheduled_days,
            'overtime_hours': self.overtime_hours,
            'overtime_pay': self.overtime_pay,
            'bonus': self.bonus,
            'allowance': self.allowance,
            'gross_pay': self.gross_pay,
            'net_pay': self.net_pay,
            'status': self.status.value,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        # Only include sensitive deduction data for HR/Finance
        if include_sensitive:
            data['deduction_absent'] = self.deduction_absent
            data['deduction_late'] = self.deduction_late
            data['deduction_other'] = self.deduction_other
            data['tax_deduction'] = self.tax_deduction
            data['social_security'] = self.social_security
            data['approved_by'] = self.approved_by
        
        return data
    
    def __repr__(self):
        return f"<PayrollRecord {self.user_id} for period {self.period_start.date()} - {self.net_pay}>"


# Need to define this after User model is imported
def setup_relationships():
    """Setup bidirectional relationship between User and PayrollRecord"""
    from .user import User
    PayrollRecordUser = User
    User.payroll_records = relationship("PayrollRecord", back_populates="payroll_records")
