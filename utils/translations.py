"""
TEAPS v5 - Bilingual Translation Utilities
Traditional Chinese and English language support with fallback mechanisms
"""
from typing import Dict, Any, Optional, Union
import json


class BilingualText:
    """
    Container for bilingual text (Traditional Chinese + English)
    Supports automatic language detection and fallback
    """
    
    LANG_TC = "zh-TW"
    LANG_EN = "en-US"
    SUPPORTED_LANGS = [LANG_TC, LANG_EN]
    
    def __init__(self, 
                 tc: str = "", 
                 en: str = "", 
                 default_lang: str = LANG_TC):
        """
        Initialize bilingual text
        
        Args:
            tc: Traditional Chinese text
            en: English text
            default_lang: Default language when one is missing
        """
        self.tc = tc or (en + " [TC]") if en else ""
        self.en = en or (tc + " [EN]") if tc else ""
        self.default_lang = default_lang
    
    def get(self, lang: str = None) -> str:
        """Get text in specified language with fallback"""
        if lang is None:
            lang = self.default_lang
        
        if lang == self.LANG_TC:
            return self.tc if self.tc else self.en
        elif lang == self.LANG_EN:
            return self.en if self.en else self.tc
        else:
            # Unknown language, return default
            return getattr(self, self.default_lang)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return {
            'zh-TW': self.tc,
            'en-US': self.en
        }
    
    def __str__(self):
        """String representation (TC first, then EN in brackets)"""
        if self.tc and self.en:
            return f"{self.tc} ({self.en})"
        return self.tc or self.en
    
    def __repr__(self):
        return f"BilingualText(tc='{self.tc}', en='{self.en}')"


class TranslationManager:
    """
    Centralized translation management for TEAPS v5
    Provides bilingual strings with automatic fallback
    """
    
    # Core system translations
    TRANSLATIONS = {
        # Authentication
        "auth.login": BilingualText(
            tc="登入",
            en="Login"
        ),
        "auth.logout": BilingualText(
            tc="登出",
            en="Logout"
        ),
        "auth.username": BilingualText(
            tc="使用者名稱",
            en="Username"
        ),
        "auth.password": BilingualText(
            tc="密碼",
            en="Password"
        ),
        "auth.invalid_credentials": BilingualText(
            tc="使用者名稱或密碼錯誤",
            en="Invalid username or password"
        ),
        
        # Attendance
        "attendance.check_in": BilingualText(
            tc="簽到",
            en="Check In"
        ),
        "attendance.check_out": BilingualText(
            tc="簽退",
            en="Check Out"
        ),
        "attendance.success": BilingualText(
            tc="簽到成功",
            en="Check-in successful"
        ),
        "attendance.failed": BilingualText(
            tc="簽到失敗",
            en="Check-in failed"
        ),
        "attendance.already_checked_in": BilingualText(
            tc("您今天已經簽到了"),
            en="You have already checked in today"
        ),
        
        # QR Code
        "qr.scan_title": BilingualText(
            tc="掃描 QR Code",
            en="Scan QR Code"
        ),
        "qr.expired": BilingualText(
            tc("QR Code 已過期"),
            en="QR Code has expired"
        ),
        "qr.invalid": BilingualText(
            tc("無效的 QR Code"),
            en="Invalid QR Code"
        ),
        "qr.used": BilingualText(
            tc("此 QR Code 已被使用過"),
            en="This QR Code has already been used"
        ),
        
        # Payroll
        "payroll.salary": BilingualText(
            tc="薪資",
            en="Salary"
        ),
        "payroll.overtime": BilingualText(
            tc="加班費",
            en="Overtime Pay"
        ),
        "payroll.net_pay": BilingualText(
            tc="實發金額",
            en="Net Pay"
        ),
        
        # Status messages
        "status.success": BilingualText(
            tc="成功",
            en="Success"
        ),
        "status.error": BilingualText(
            tc("錯誤"),
            en="Error"
        ),
        "status.pending": BilingualText(
            tc("待審核"),
            en="Pending"
        ),
        "status.approved": BilingualText(
            tc("已核准"),
            en="Approved"
        ),
        "status.rejected": BilingualText(
            tc("已拒絕"),
            en="Rejected"
        ),
        
        # Common UI elements
        "ui.submit": BilingualText(
            tc="提交",
            en="Submit"
        ),
        "ui.cancel": BilingualText(
            tc="取消",
            en="Cancel"
        ),
        "ui.confirm": BilingualText(
            tc("確認"),
            en="Confirm"
        ),
        "ui.back": BilingualText(
            tc("返回"),
            en="Back"
        ),
        
        # Date/Time
        "date.today": BilingualText(
            tc="今天",
            en="Today"
        ),
        "date.yesterday": BilingualText(
            tc="昨天",
            en="Yesterday"
        ),
        "time.now": BilingualText(
            tc="現在",
            en="Now"
        ),
    }
    
    @classmethod
    def get(cls, key: str, lang: str = None) -> str:
        """Get translated text by key"""
        if key not in cls.TRANSLATIONS:
            return f"[{key}]"  # Return key as fallback
        
        translation = cls.TRANSLATIONS[key]
        return translation.get(lang)
    
    @classmethod
    def get_dict(cls, key: str, lang: str = None) -> Dict[str, str]:
        """Get full bilingual dictionary for a key"""
        if key not in cls.TRANSLATIONS:
            return {'zh-TW': f'[{key}]', 'en-US': f'[{key}]'}
        
        translation = cls.TRANSLATIONS[key]
        return translation.to_dict()
    
    @classmethod
    def add_translation(cls, key: str, tc: str, en: str):
        """Add or update a translation"""
        cls.TRANSLATIONS[key] = BilingualText(tc=tc, en=en)
    
    @classmethod
    def list_keys(cls, category: str = None) -> list:
        """List all available translation keys (optionally filtered by category)"""
        if category is None:
            return list(cls.TRANSLATIONS.keys())
        
        # Filter by prefix
        return [key for key in cls.TRANSLATIONS.keys() if key.startswith(category)]


def t(key: str, lang: str = None) -> str:
    """Convenience function for translation lookup"""
    return TranslationManager.get(key, lang)


def _init_default_translations():
    """Initialize default translations (called at module load)"""
    # This ensures all standard translations are available
    pass
