"""
TEAPS v5 - Telegram Bot Implementation (No QR Code)
Text-based interaction with inline keyboard menus and manager approval workflow
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from typing import Dict, Any, Optional
import os
import sys

# Add project root to path
sys.path.insert(0, str(__import__('pathlib').Path.home() / ".hermes" / "teaps" / "v5"))

from handlers.bot_handlers import (
    AttendanceHandler, 
    PayrollHandler, 
    AdminHandler,
    BOT_COMMANDS,
    get_bot_commands_description,
    BotState
)
from utils.translations import t


class TEAPSBot:
    """TEAPS Telegram Bot wrapper - Text-based interaction"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv('TEAPS_TELEGRAM_BOT_TOKEN')
        
        if not self.token:
            raise ValueError("Telegram bot token not found. Set TEAPS_TELEGRAM_BOT_TOKEN env var.")
        
        # Initialize handlers (will be set with dependencies later)
        self.db_session_func = None
        self.attendance_handler = AttendanceHandler(self.db_session_func)
        self.payroll_handler = PayrollHandler(self.db_session_func)
        self.admin_handler = AdminHandler(self.db_session_func)
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Setup command handlers
        self._setup_handlers()
    
    def set_dependencies(self, db_session_func):
        """Set dependencies after initialization"""
        self.db_session_func = db_session_func
        self.attendance_handler = AttendanceHandler(db_session_func)
        self.payroll_handler = PayrollHandler(db_session_func)
        self.admin_handler = AdminHandler(db_session_func)
    
    def _setup_handlers(self):
        """Setup all command handlers"""
        
        # Start command
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Help command
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Attendance commands
        self.application.add_handler(CommandHandler("checkin", self.checkin_command))
        self.application.add_handler(CommandHandler("checkout", self.checkout_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        
        # Payroll command
        self.application.add_handler(CommandHandler("payroll", self.payroll_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("approve_list", self.approve_list_command))
        
        # Callback queries for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.callback_query_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_msg = (
            f"👋 歡迎使用 TEAPS v5 - Attendance & Payroll System!\n\n"
            f"Hi {user.first_name}! 👋\n\n"
            "可用命令：\n"
            "/checkin - 簽到\n"
            "/checkout - 簽退\n"
            "/status - 查詢今日出勤狀態\n"
            "/history - 查詢歷史記錄\n"
            "/payroll - 查詢薪資資訊\n"
            "/help - 顯示幫助訊息\n\n"
            "管理員還有更多權限！"
        )
        
        await update.message.reply_text(welcome_msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📚 TEAPS v5 幫助訊息\n\n"
            "**簽到功能**:\n"
            "/checkin - 掃描 QR Code 簽到\n"
            "/checkout - 掃描 QR Code 簽退\n"
            "/status - 查看今天的出勤狀態\n"
            "/history [日期範圍] - 查詢歷史記錄\n\n"
            
            "**薪資功能**:\n"
            "/payroll - 查看本月薪資明細\n\n"
            
            "**管理員命令** (僅限管理員):\n"
            "/approve <record_id> - 核准出勤記錄\n"
            "/reject <record_id> - 拒絕出勤記錄\n"
            "/export [月份] - 匯出報表\n\n"
            
            "💡 提示：請確保已正確設定員工編號和部門"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def checkin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /checkin command"""
        user = update.effective_user
        
        # TODO: Get actual user_id from database using Telegram chat ID
        user_id = 1  # Placeholder
        
        message = await self.attendance_handler.handle_checkin(
            str(user.id), 
            user_id
        )
        
        await update.message.reply_text(message)
    
    async def checkout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /checkout command"""
        await update.message.reply_text("簽退功能開發中...")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show today's attendance status"""
        user = update.effective_user
        
        # TODO: Query actual database for user's status
        message = (
            f"📅 今日出勤狀態\n\n"
            f"員工：{user.first_name}\n"
            f"簽到時間：尚未簽到\n"
            f"狀態：待簽到"
        )
        
        await update.message.reply_text(message)
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        args = context.args
        
        if len(args) >= 2:
            start_date = args[0]
            end_date = args[1]
            
            message = f"📊 出勤歷史記錄\n\n"
            message += f"日期範圍：{start_date} ~ {end_date}\n"
            message += "\n查詢功能開發中..."
        else:
            message = "用法：/history <開始日期> <結束日期>\n例如：/history 2026-04-01 2026-04-30"
        
        await update.message.reply_text(message)
    
    async def payroll_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /payroll command"""
        user = update.effective_user
        
        message = await self.payroll_handler.handle_payroll(
            str(user.id),
            int(user.id)  # Placeholder user_id
        )
        
        await update.message.reply_text(message)
    
    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /approve command (admin only)"""
        args = context.args
        
        if not args or len(args) < 1:
            await update.message.reply_text("用法：/approve <record_id>")
            return
        
        try:
            record_id = int(args[0])
            
            # TODO: Check if user is admin
            
            result = await self.admin_handler.handle_approve(
                str(update.effective_user.id),
                int(update.effective_user.id),
                record_id,
                approve=True
            )
            
            await update.message.reply_text(result)
        
        except ValueError:
            await update.message.reply_text("無效的記錄 ID")
    
    async def reject_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reject command (admin only)"""
        args = context.args
        
        if not args or len(args) < 1:
            await update.message.reply_text("用法：/reject <record_id>")
            return
        
        try:
            record_id = int(args[0])
            
            result = await self.admin_handler.handle_approve(
                str(update.effective_user.id),
                int(update.effective_user.id),
                record_id,
                approve=False
            )
            
            await update.message.reply_text(result)
        
        except ValueError:
            await update.message.reply_text("無效的記錄 ID")
    
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /export command (admin only)"""
        args = context.args
        
        if not args:
            from datetime import datetime
            current_month = datetime.now().strftime("%Y-%m")
            await update.message.reply_text(f"匯出本月報表：{current_month}")
        else:
            await update.message.reply_text(f"匯出報表：{args[0]}")
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        chat_id = str(query.message.chat_id)
        
        # Handle check-in confirmation
        if query.data == "confirm_checkin_yes":
            from datetime import datetime
            message = (
                f"✅ 簽到成功！\n\n"
                f"員工 ID: {query.from_user.id}\n"
                f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"狀態：⏳ 待上級核准\n\n"
                f"請等待管理員確認後生效。"
            )
            await query.message.edit_text(message)
            
        elif query.data == "confirm_checkin_no":
            message = "❌ 已取消簽到"
            await query.message.edit_text(message)
        
        # Handle check-out confirmation
        elif query.data == "confirm_checkout_yes":
            from datetime import datetime
            message = (
                f"✅ 簽退成功！\n\n"
                f"員工 ID: {query.from_user.id}\n"
                f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"狀態：⏳ 待上級核准\n\n"
                f"請等待管理員確認後生效。"
            )
            await query.message.edit_text(message)
            
        elif query.data == "confirm_checkout_no":
            message = "❌ 已取消簽退"
            await query.message.edit_text(message)
        
        # Handle approve/reject buttons from admin list
        elif query.data.startswith("approve_yes_"):
            record_id = int(query.data.split("_")[-1])
            
            try:
                with self.attendance_handler.db() as session:
                    from models.attendance import AttendanceRecord, AttendanceStatus
                    
                    record = session.query(AttendanceRecord).filter_by(id=record_id).first()
                    
                    if not record:
                        await query.message.edit_text("❌ 記錄不存在")
                        return
                    
                    record.status = AttendanceStatus.APPROVED
                    session.commit()
                
                user_name = record.user.name_tc if record.user else f"員工 {record.user_id}"
                message = f"✅ {user_name} 的出勤記錄已核准！\n\n請重新整理查看最新狀態。"
                await query.message.edit_text(message)
            
            except Exception as e:
                await query.message.edit_text(f"❌ 處理失敗：{str(e)}")
        
        elif query.data.startswith("reject_no_"):
            record_id = int(query.data.split("_")[-1])
            
            try:
                with self.attendance_handler.db() as session:
                    from models.attendance import AttendanceRecord, AttendanceStatus
                    
                    record = session.query(AttendanceRecord).filter_by(id=record_id).first()
                    
                    if not record:
                        await query.message.edit_text("❌ 記錄不存在")
                        return
                    
                    record.status = AttendanceStatus.REJECTED
                    session.commit()
                
                user_name = record.user.name_tc if record.user else f"員工 {record.user_id}"
                message = f"❌ {user_name} 的出勤記錄已拒絕。\n\n請通知員工重新提交。"
                await query.message.edit_text(message)
            
            except Exception as e:
                await query.message.edit_text(f"❌ 處理失敗：{str(e)}")
        
        else:
            # Unknown callback
            await query.answer("未知操作，請聯繫管理員", show_alert=True)
    
    def run(self):
        """Start the bot"""
        print("🤖 Starting TEAPS Telegram Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Singleton instance
_bot_instance = None

def get_bot() -> Optional[TEAPSBot]:
    """Get or create singleton bot instance"""
    global _bot_instance
    if _bot_instance is None:
        try:
            _bot_instance = TEAPSBot()
        except ValueError as e:
            print(f"⚠️  {e}")
            return None
    return _bot_instance


if __name__ == "__main__":
    bot = get_bot()
    if bot:
        bot.run()
