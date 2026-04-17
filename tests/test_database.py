"""
TEAPS v5 - Database Utility Tests
Test retry mechanisms and sensitive data filtering
"""
import pytest
import json


class TestSanitizeLogData:
    """Test sensitive data sanitization functionality"""
    
    @pytest.fixture
    def sanitize_func(self):
        from utils.database import sanitize_log_data
        return sanitize_func
    
    def test_basic_sanitization(self, sanitize_func):
        """Test basic password/token field removal"""
        data = {
            'user_id': 123,
            'username': 'john',
            'password': 'secret123',
            'token': 'abc-def-ghi'
        }
        
        sanitized = sanitize_func(data)
        
        assert sanitized['user_id'] == 123
        assert sanitized['username'] == 'john'
        assert sanitized['password'] == '***REDACTED***'
        assert sanitized['token'] == '***REDACTED***'
    
    def test_nested_dict_sanitization(self, sanitize_func):
        """Test sanitization of nested dictionaries"""
        data = {
            'user': {
                'name': 'Jane',
                'password': 'nested_secret'
            },
            'session': {
                'token': 'session_token_123',
                'expires_at': '2026-12-31'
            }
        }
        
        sanitized = sanitize_func(data)
        
        assert sanitized['user']['name'] == 'Jane'
        assert sanitized['user']['password'] == '***REDACTED***'
        assert sanitized['session']['token'] == '***REDACTED***'
        assert sanitized['session']['expires_at'] == '2026-12-31'
    
    def test_list_sanitization(self, sanitize_func):
        """Test sanitization of lists containing sensitive data"""
        data = {
            'records': [
                {'id': 1, 'password': 'pass1'},
                {'id': 2, 'token': 'tok2'},
                {'id': 3, 'safe': 'value'}
            ]
        }
        
        sanitized = sanitize_func(data)
        
        assert sanitized['records'][0]['password'] == '***REDACTED***'
        assert sanitized['records'][1]['token'] == '***REDACTED***'
        assert sanitized['records'][2]['safe'] == 'value'
    
    def test_custom_exclude_fields(self, sanitize_func):
        """Test custom field exclusion"""
        data = {
            'user_id': 456,
            'ssn': '123-45-6789',
            'credit_card': '4111-1111-1111-1111'
        }
        
        sanitized = sanitize_func(data, exclude_fields=['user_id'])
        
        assert sanitized['user_id'] == '***REDACTED***'  # Custom exclusion
        assert sanitized['ssn'] == '***REDACTED***'  # Built-in exclusion
        assert sanitized['credit_card'] == '***REDACTED***'  # Built-in exclusion
    
    def test_non_sensitive_data_unchanged(self, sanitize_func):
        """Test that non-sensitive data remains intact"""
        data = {
            'employee_id': 'EMP001',
            'name_tc': '陳小明',
            'name_en': 'Xiao-Ming Chen',
            'email': 'xiao.chen@company.com',
            'department': 'Engineering'
        }
        
        sanitized = sanitize_func(data)
        
        assert sanitized == data
    
    def test_empty_data(self, sanitize_func):
        """Test sanitization of empty/edge case data"""
        assert sanitize_func({}) == {}
        assert sanitize_func(None) is None
        assert sanitize_func("") == ""
        assert sanitize_func(123) == 123


class TestDatabaseRetryMechanism:
    """Test database retry decorator functionality"""
    
    @pytest.fixture
    def retry_func(self):
        from utils.database import retry_on_failure
        return retry_func
    
    def test_successful_call_no_retry(self, retry_func):
        """Test that successful calls don't trigger retries"""
        call_count = 0
        
        @retry_func(max_attempts=3)
        def operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = operation()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self, retry_func):
        """Test that retries occur on failure"""
        call_count = 0
        
        @retry_func(max_attempts=3, delay=0.1)
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success after retries"
        
        result = operation()
        
        assert result == "success after retries"
        assert call_count == 3
    
    def test_max_attempts_exceeded(self, retry_func):
        """Test that max attempts raises RuntimeError"""
        call_count = 0
        
        @retry_func(max_attempts=2, delay=0.1)
        def operation():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")
        
        with pytest.raises(RuntimeError) as exc_info:
            operation()
        
        assert "failed after 2 attempts" in str(exc_info.value)
        assert call_count == 2


class TestUserModel:
    """Test User model functionality"""
    
    @pytest.fixture
    def user_model(self):
        from models.user import User, UserRole
        return User, UserRole
    
    def test_password_hashing(self, user_model):
        """Test bcrypt password hashing"""
        User, _ = user_model
        
        user = User(
            employee_id="TEST001",
            name_tc="測試使用者",
            name_en="Test User",
            email="test@example.com"
        )
        
        # Set password
        user.set_password("SecurePassword123!")
        
        # Verify hash is set and not plain text
        assert user.password_hash is not None
        assert len(user.password_hash) > 50  # bcrypt hashes are long
        assert "SecurePassword123!" not in user.password_hash
    
    def test_password_verification(self, user_model):
        """Test password verification"""
        User, _ = user_model
        
        user = User(
            employee_id="TEST002",
            name_tc="驗證使用者",
            name_en="Verify User",
            email="verify@example.com"
        )
        
        user.set_password("MyPassword456")
        
        # Correct password should return True
        assert user.check_password("MyPassword456") == True
        
        # Wrong password should return False
        assert user.check_password("WrongPassword") == False
    
    def test_user_to_dict(self, user_model):
        """Test user dictionary conversion"""
        User, _ = user_model
        
        user = User(
            employee_id="TEST003",
            name_tc="轉換使用者",
            name_en="Convert User",
            email="convert@example.com"
        )
        
        # Test without sensitive data
        user_dict = user.to_dict(include_sensitive=False)
        
        assert 'id' in user_dict
        assert 'employee_id' in user_dict
        assert 'password_hash' not in user_dict
        
        # Test with sensitive data (only if explicitly requested)
        user.set_password("TestPass")
        user_dict_sensitive = user.to_dict(include_sensitive=True)
        
        assert 'password_hash' in user_dict_sensitive


class TestAttendanceModel:
    """Test AttendanceRecord model functionality"""
    
    @pytest.fixture
    def attendance_model(self):
        from models.attendance import AttendanceRecord, CheckType, AttendanceStatus
        return AttendanceRecord, CheckType, AttendanceStatus
    
    def test_working_hours_calculation(self, attendance_model):
        """Test actual working hours calculation"""
        from datetime import datetime, timedelta
        
        AttendanceRecord, _, _ = attendance_model
        
        record = AttendanceRecord(
            user_id=1,
            date=datetime.now()
        )
        
        # Set check-in/out times (8 hour workday)
        start_time = datetime(2026, 4, 17, 9, 0, 0)
        end_time = datetime(2026, 4, 17, 18, 0, 0)
        
        record.check_in_time = start_time
        record.check_out_time = end_time
        record.break_duration_minutes = 60
        
        hours = record.calculate_working_hours()
        
        # Should be 9 hours - 1 hour break = 8 hours
        assert hours == 8.0
    
    def test_partial_day_calculation(self, attendance_model):
        """Test partial day working hours"""
        from datetime import datetime
        
        AttendanceRecord, _, _ = attendance_model
        
        record = AttendanceRecord(user_id=2, date=datetime.now())
        
        start_time = datetime(2026, 4, 17, 10, 0, 0)
        end_time = datetime(2026, 4, 17, 15, 30, 0)
        
        record.check_in_time = start_time
        record.check_out_time = end_time
        record.break_duration_minutes = 30
        
        hours = record.calculate_working_hours()
        
        # 5.5 hours - 0.5 hour break = 5 hours
        assert hours == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

