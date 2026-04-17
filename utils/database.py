"""
TEAPS v5 - Database Utilities
Includes retry mechanisms and sensitive data sanitization
"""
import json
from functools import wraps
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import os
import time

# Sensitive field patterns to filter from logs
SENSITIVE_FIELDS = {
    'password', 'token', 'secret', 'api_key', 'credit_card', 
    'cvv', 'ssn', 'salary', 'bank_account'
}


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying database operations with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each failure
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, SQLAlchemyError) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            # All attempts failed
            raise RuntimeError(
                f"Database operation failed after {max_attempts} attempts: {str(last_exception)}"
            )
        
        return wrapper
    return decorator


def sanitize_log_data(data: Any, exclude_fields: Optional[List[str]] = None) -> Any:
    """
    Recursively sanitize data by removing or masking sensitive fields
    
    Args:
        data: Data to sanitize (dict, list, tuple, or primitive)
        exclude_fields: Additional fields to exclude (beyond SENSITIVE_FIELDS)
    
    Returns:
        Sanitized copy of the data with sensitive information masked
    """
    if exclude_fields is None:
        exclude_fields = []
    
    all_sensitive = SENSITIVE_FIELDS.union(set(exclude_fields))
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if this field name contains any sensitive pattern
            if any(pattern in key.lower() for pattern in all_sensitive):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = sanitize_log_data(value, exclude_fields)
        return sanitized
    
    elif isinstance(data, (list, tuple)):
        return [sanitize_log_data(item, exclude_fields) for item in data]
    
    else:
        # Primitive types (str, int, float, bool, None) - return as-is
        return data


def get_database_url() -> str:
    """Get database URL from environment variables"""
    default_config = {
        'DB_HOST': os.getenv('TEAPS_DB_HOST', 'localhost'),
        'DB_PORT': os.getenv('TEAPS_DB_PORT', '3306'),
        'DB_NAME': os.getenv('TEAPS_DB_NAME', 'teaps_v5'),
        'DB_USER': os.getenv('TEAPS_DB_USER', 'root'),
        'DB_PASSWORD': os.getenv('TEAPS_DB_PASSWORD', ''),
    }
    
    return (
        f"mysql+pymysql://{default_config['DB_USER']}:"
        f"{default_config['DB_PASSWORD']}@"
        f"{default_config['DB_HOST']}:{default_config['DB_PORT']}/"
        f"{default_config['DB_NAME']}?charset=utf8mb4"
    )


@retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
def create_all_tables(engine):
    """Create all database tables if they don't exist"""
    from .models import Base
    Base.metadata.create_all(bind=engine)


@retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
def get_session():
    """Get a new database session with proper cleanup"""
    from sqlalchemy.orm import Session
    
    db_url = get_database_url()
    engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def log_query(session: Session, query_info: Dict[str, Any]):
    """
    Log database query with automatic sanitization of sensitive data
    
    Args:
        session: SQLAlchemy session
        query_info: Dictionary containing query information
    """
    sanitized_info = sanitize_log_data(query_info)
    
    # In production, this would write to a proper logging system
    print(f"[DB Query] {json.dumps(sanitized_info, ensure_ascii=False)}")


def execute_query(session: Session, sql: str, params: Optional[Dict] = None):
    """
    Execute raw SQL query with error handling and logging
    
    Args:
        session: SQLAlchemy session
        sql: SQL statement to execute
        params: Query parameters (if any)
    
    Returns:
        Query result rows
    """
    try:
        if params:
            result = session.execute(text(sql), params)
        else:
            result = session.execute(text(sql))
        
        session.commit()
        return result.fetchall()
    
    except Exception as e:
        session.rollback()
        print(f"[DB Error] {str(e)}")
        raise


def bulk_insert_with_retry(session, model_class, data_list: List[Dict], max_attempts: int = 3):
    """
    Bulk insert records with retry mechanism
    
    Args:
        session: SQLAlchemy session
        model_class: SQLAlchemy model class
        data_list: List of dictionaries to insert
        max_attempts: Maximum retry attempts
    
    Returns:
        Number of successfully inserted records
    """
    for attempt in range(1, max_attempts + 1):
        try:
            # Convert dicts to model instances
            instances = [model_class(**data) for data in data_list]
            
            session.add_all(instances)
            session.commit()
            
            return len(instances)
        
        except Exception as e:
            if attempt == max_attempts:
                print(f"[Bulk Insert Failed] {str(e)}")
                session.rollback()
                return 0
            
            # Wait before retry
            time.sleep(1 * attempt)
