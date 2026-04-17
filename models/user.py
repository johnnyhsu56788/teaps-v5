"""
TEAPS v5 - User and Department Models
SQLAlchemy ORM models for user management and organizational structure
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base
import enum
import bcrypt

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User role hierarchy"""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """User model with bilingual support and authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)  # 員工編號
    name_tc = Column(String(100), nullable=False)  # 中文姓名
    name_en = Column(String(100), nullable=False)  # English name
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="employees")
    attendance_records = relationship("AttendanceRecord", back_populates="user", cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        """Hash and set password using bcrypt"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary (sanitize sensitive data)"""
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'name_tc': self.name_tc,
            'name_en': self.name_en,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.value,
            'department_id': self.department_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    def __repr__(self):
        return f"<User {self.employee_id}: {self.name_tc} ({self.role.value})>"


class Department(Base):
    """Department/Organization unit model"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_tc = Column(String(200), nullable=False)  # 中文名稱
    name_en = Column(String(200), nullable=False)  # English name
    code = Column(String(50), unique=True, nullable=False)  # Department code
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = relationship("User", foreign_keys=[manager_id], backref="managed_departments")
    employees = relationship("User", back_populates="department")
    
    def to_dict(self) -> dict:
        """Convert department to dictionary"""
        return {
            'id': self.id,
            'name_tc': self.name_tc,
            'name_en': self.name_en,
            'code': self.code,
            'manager_id': self.manager_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<Department {self.code}: {self.name_tc}>"
