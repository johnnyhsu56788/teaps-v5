"""
TEAPS v5 - Telegram Bot Handlers (Text-based, No QR Code)
FSM-based handlers for attendance check-in/out via interactive menus
All records require manager approval before becoming active
"""
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

# Import TEAPS components
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / ".hermes" / "teaps" / "v5"))


class BotState(Enum):
    """Finite State Machine states for bot interactions"""
    IDLE = "idle"
    CONFIRM_CHECK_IN = "confirm_check_in"
    CONFIRM_CHECK_OUT = "confirm_check_out"
    SELECT_DATE_RANGE = "select_date_range"
    APPROVE_ATTENDANCE = "approve_attendance"
    REJECT_ATTENDANCE = "reject_attendance"


@dataclass
class UserSession:
    """User session data for FSM"""
    user_id: int
    telegram_chat_id: str
    state: BotState = BotState.IDLE
    temp_data: Dict[str, Any] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.temp_data is None:
            self.temp_data = {}
        if self.created_at is None:
            import time
            self.created_at = time.time()


class SessionStore:
    """In-memory session storage (use Redis in production)"""
    
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
    
    def get_session(self, chat_id: str) -> Optional[UserSession]:
        """Get or create session for a user"""
        if chat_id not in self._sessions:
            # Extract user ID from chat_id (simplified - in production use DB lookup)
            user_id = int(chat_id.split(':')[-1]) if ':' in chat_id else 0
            
            self._sessions[chat_id] = UserSession(
                user_id=user_id,
                telegram_chat_id=chat_id
            )
        
        return self._sessions[chat_id]
    
    def update_state(self, chat_id: str, state: BotState):
        """Update session state"""
        if chat_id in self._sessions:
            self._sessions[chat_id].state = state
    
    def set_temp_data(self, chat_id: str, key: str, value: Any):
        """Set temporary data for current interaction"""
        if chat_id in self._sessions:
            self._sessions[chat_id].temp_data[key] = value
    
    def get_temp_data(self, chat_id: str, key: str) -> Optional[Any]:
        """Get temporary data"""
        if chat_id in self._sessions:
            return self._sessions[chat_id].temp_data.get(key)
    
    def clear_session(self, chat_id: str):
        """Clear session data (e.g., after /cancel)"""
        if chat_id in self._sessions:
            session = self._sessions[chat_id]
            session.state = BotState.IDLE
            session.temp_data.clear()


class AttendanceHandler:
    """Handle attendance-related bot commands with inline keyboard menus"""
    
    def __init__(self, db_session_func):
        self.db = db_session_func
        self.sessions = SessionStore()
    
    async def handle_checkin(self, chat_id: str, user_id: int) -> tuple[str, dict]:
        """
        Handle /checkin command - show confirmation menu
        
        Returns:
            Tuple of (message_text, inline_keyboard_markup)
        """
        from utils.translations import t
        
        # Store intent in session
        self.sessions.update_state(chat_id, BotState.CONFIRM_CHECK_IN)
        
        message = (
            f"👋 歡迎使用簽到系統！\n\n"
            f"您想現在簽到嗎？\n\n"
            f"員工：{user_id}\n"
            f"日期：{__import__('datetime').date.today()}"
        )
        
        # Create inline keyboard with confirmation buttons
        keyboard = [
            [
                {"text": "✅ 確認簽到", "callback_data": "confirm_checkin_yes"},
                {"text": "❌ 取消", "callback_data": "confirm_checkin_no"}
            ]
        ]
        
        return message, {"inline_keyboard": keyboard}
    
    async def handle_checkout(self, chat_id: str, user_id: int) -> tuple[str, dict]:
        """Handle /checkout command - show confirmation menu"""
        from utils.translations import t
        
        self.sessions.update_state(chat_id, BotState.CONFIRM_CHECK_OUT)
        
        message = (
            f"👋 歡迎使用簽退系統！\n\n"
            f"您想現在簽退嗎？\n\n"
            f"員工：{user_id}\n"
            f"日期：{__import__('datetime').date.today()}"
        )
        
        keyboard = [
            [
                {"text": "✅ 確認簽退", "callback_data": "confirm_checkout_yes"},
                {"text": "❌ 取消", "callback_data": "confirm_checkout_no"}
            ]
        ]
        
        return message, {"inline_keyboard": keyboard}
    
    async def handle_status(self, chat_id: str, user_id: int) -> str:
        """Handle /status command - show today's attendance status"""
        try:
            with self.db() as session:
                from models.attendance import AttendanceRecord
                
                today = __import__('datetime').date.today().isoformat()
                
                record = session.query(AttendanceRecord).filter_by(
                    user_id=user_id,
                    date=today
                ).first()
                
                if not record:
                    return "📅 今日尚未簽到\n\n請使用 /checkin 開始簽到"
                
                check_in = record.check_in_time.strftime("%H:%M") if record.check_in_time else "未簽入"
                check_out = record.check_out_time.strftime("%H:%M") if record.check_out_time else "未簽出"
                
                status_map = {
                    'pending': '⏳ 待核准',
                    'approved': '✅ 已核准',
                    'rejected': '❌ 已拒絕'
                }
                
                return (
                    f"📅 今日出勤狀態\n\n"
                    f"員工：{user_id}\n"
                    f"簽到時間：{check_in}\n"
                    f"簽退時間：{check_out}\n"
                    f"狀態：{status_map.get(record.status.value, '未知')}"
                )
        
        except Exception as e:
            return f"❌ 查詢失敗：{str(e)}"
    
    async def handle_history(self, chat_id: str, user_id: int, 
                            start_date: str = None, end_date: str = None) -> str:
        """Handle /history command - show historical records"""
        try:
            with self.db() as session:
                from models.attendance import AttendanceRecord
                
                query = session.query(AttendanceRecord).filter_by(user_id=user_id)
                
                if start_date and end_date:
                    query = query.filter(
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date
                    )
                elif start_date:
                    query = query.filter(AttendanceRecord.date >= start_date)
                
                records = query.order_by(AttendanceRecord.date.desc()).limit(10).all()
                
                if not records:
                    return "📭 找不到歷史記錄"
                
                lines = ["📊 出勤歷史記錄 (最近 10 筆):\n"]
                for record in records:
                    date_str = record.date.strftime("%Y-%m-%d")
                    check_in = record.check_in_time.strftime("%H:%M") if record.check_in_time else "-"
                    check_out = record.check_out_time.strftime("%H:%M") if record.check_out_time else "-"
                    
                    status_map = {
                        'pending': '⏳ 待核准',
                        'approved': '✅ 已核准',
                        'rejected': '❌ 已拒絕'
                    }
                    
                    lines.append(
                        f"{date_str} | 簽到: {check_in} | 簽退: {check_out} | "
                        f"狀態：{status_map.get(record.status.value, '未知')}"
                    )
                
                return "\n".join(lines)
        
        except Exception as e:
            return f"❌ 查詢失敗：{str(e)}"


class PayrollHandler:
    """Handle payroll-related bot commands"""
    
    def __init__(self, db_session_func):
        self.db = db_session_func
    
    async def handle_payroll(self, chat_id: str, user_id: int) -> str:
        """Handle /payroll command - show current month's salary summary"""
        try:
            with self.db() as session:
                from models.payroll import PayrollRecord
                
                now = __import__('datetime').datetime.now()
                year_month = f"{now.year}-{now.month:02d}"
                
                record = session.query(PayrollRecord).filter(
                    PayrollRecord.user_id == user_id,
                    PayrollRecord.period_start.like(f"{year_month}%")
                ).first()
                
                if not record:
                    return (
                        f"💰 本月薪資查詢\n\n"
                        f"目前尚未計算薪資，請於次月查看。\n\n"
                        f"月份：{now.year}/{now.month:02d}"
                    )
                
                return (
                    f"💰 {year_month} 薪資明細\n\n"
                    f"基本工資：${record.base_salary:,.0f}\n"
                    f"加班費：${record.overtime_pay:,.0f}\n"
                    f"獎金：${record.bonus:,.0f}\n"
                    f"扣款：-${record.deduction_absent + record.deduction_late + record.tax_deduction:,.0f}\n"
                    f"─────────────\n"
                    f"實發金額：${record.net_pay:,.0f}"
                )
        
        except Exception as e:
            return f"❌ 查詢失敗：{str(e)}"


class AdminHandler:
    """Handle admin-specific commands for approval/rejection"""
    
    def __init__(self, db_session_func):
        self.db = db_session_func
    
    async def handle_approve(self, chat_id: str, user_id: int, 
                            record_id: int) -> tuple[str, dict]:
        """Handle approve request - show confirmation menu"""
        try:
            with self.db() as session:
                from models.attendance import AttendanceRecord
                
                record = session.query(AttendanceRecord).filter_by(id=record_id).first()
                
                if not record:
                    return "❌ 找不到該筆出勤記錄", None
                
                user_name = record.user.name_tc if record.user else f"員工 {user_id}"
                
                message = (
                    f"📋 核准出勤記錄\n\n"
                    f"員工：{user_name}\n"
                    f"日期：{record.date.strftime('%Y-%m-%d')}\n"
                    f"簽到時間：{record.check_in_time.strftime('%H:%M') if record.check_in_time else '未簽入'}\n"
                    f"簽退時間：{record.check_out_time.strftime('%H:%M') if record.check_out_time else '未簽出'}\n\n"
                    f"是否核准此記錄？"
                )
                
                keyboard = [
                    [
                        {"text": "✅ 核准", "callback_data": f"approve_yes_{record_id}"},
                        {"text": "❌ 拒絕", "callback_data": f"approve_no_{record_id}"}
                    ]
                ]
                
                return message, {"inline_keyboard": keyboard}
        
        except Exception as e:
            return f"❌ 處理失敗：{str(e)}", None
    
    async def handle_reject(self, chat_id: str, user_id: int, 
                           record_id: int) -> tuple[str, dict]:
        """Handle reject request - show confirmation menu"""
        try:
            with self.db() as session:
                from models.attendance import AttendanceRecord
                
                record = session.query(AttendanceRecord).filter_by(id=record_id).first()
                
                if not record:
                    return "❌ 找不到該筆出勤記錄", None
                
                user_name = record.user.name_tc if record.user else f"員工 {user_id}"
                
                message = (
                    f"📋 拒絕出勤記錄\n\n"
                    f"員工：{user_name}\n"
                    f"日期：{record.date.strftime('%Y-%m-%d')}\n\n"
                    f"請輸入拒絕原因（可選）："
                )
                
                # Store record_id in session for follow-up
                self.sessions.set_temp_data(chat_id, "reject_record_id", record_id)
                
                return message, None
        
        except Exception as e:
            return f"❌ 處理失敗：{str(e)}", None
    
    async def handle_list_pending(self, chat_id: str, user_id: int) -> tuple[str, dict]:
        """List all pending attendance records for approval"""
        try:
            with self.db() as session:
                from models.attendance import AttendanceRecord
                
                # Get today's pending records
                today = __import__('datetime').date.today().isoformat()
                
                records = session.query(AttendanceRecord).filter_by(
                    date=today,
                    status='pending'
                ).all()
                
                if not records:
                    return "✅ 今日所有記錄已處理完畢", None
                
                # Build inline keyboard with all pending records
                lines = ["📋 待核准的出勤記錄:\n"]
                keyboard_buttons = []
                
                for idx, record in enumerate(records):
                    user_name = record.user.name_tc if record.user else f"員工 {record.user_id}"
                    check_in = record.check_in_time.strftime("%H:%M") if record.check_in_time else "未簽入"
                    
                    lines.append(f"{idx + 1}. {user_name} - 簽到: {check_in}")
                    
                    # Add buttons for each record
                    keyboard_buttons.append([
                        {"text": f"✅ {record.id}", "callback_data": f"approve_yes_{record.id}"},
                        {"text": f"❌ {record.id}", "callback_data": f"reject_no_{record.id}"}
                    ])
                
                message = "\n".join(lines) + "\n\n請點擊按鈕進行核准或拒絕"
                
                return message, {"inline_keyboard": keyboard_buttons} if keyboard_buttons else None
        
        except Exception as e:
            return f"❌ 查詢失敗：{str(e)}", None


# Bot command definitions with bilingual support
BOT_COMMANDS = [
    {
        "command": "start",
        "description_tc": "開始使用 TEAPS 系統",
        "description_en": "Start using TEAPS system"
    },
    {
        "command": "help",
        "description_tc": "顯示幫助訊息",
        "description_en": "Show help message"
    },
    {
        "command": "checkin",
        "description_tc": "簽到 (需上級核准)",
        "description_en": "Check in (requires approval)"
    },
    {
        "command": "checkout",
        "description_tc": "簽退 (需上級核准)",
        "description_en": "Check out (requires approval)"
    },
    {
        "command": "status",
        "description_tc": "查詢今日出勤狀態",
        "description_en": "Query today's attendance status"
    },
    {
        "command": "history",
        "description_tc": "查詢歷史出勤記錄",
        "description_en": "Query historical attendance records"
    },
    {
        "command": "payroll",
        "description_tc": "查詢薪資資訊",
        "description_en": "Query payroll information"
    },
    # Admin commands (only for managers/admins)
    {
        "command": "approve_list",
        "description_tc": "查看待核准記錄",
        "description_en": "View pending records to approve"
    },
]


def get_bot_commands_description(lang: str = "zh-TW") -> list:
    """Get bot commands list in specified language"""
    if lang == "en-US":
        return [
            {"command": cmd["command"], "description": cmd["description_en"]}
            for cmd in BOT_COMMANDS
        ]
    
    # Default to Traditional Chinese
    return [
        {"command": cmd["command"], "description": cmd["description_tc"]}
        for cmd in BOT_COMMANDS
    ]
