import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (
    get_or_create_user, create_file_record, get_file_by_short_link_id,
    get_user_stats, get_all_users_stats, get_cpm_rates, update_cpm_rates,
    create_withdrawal_request, get_user_withdrawals, get_pending_withdrawals,
    approve_withdrawal, reject_withdrawal, get_withdrawal_by_id, get_ad_codes, update_ad_code, remove_ad_code,
    get_referral_stats, award_referral_commission, get_user_files, get_file_stats,
    delete_file, delete_file_by_short_link, get_file_count
)
from dotenv import load_dotenv
import secrets

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

def get_base_url():
    replit_domains = os.getenv('REPLIT_DOMAINS')
    if replit_domains:
        domains = replit_domains.split(',')
        return f"https://{domains[0]}"
    return os.getenv('BASE_URL', 'http://localhost:5000')

BASE_URL = get_base_url()
BOT_USERNAME = os.getenv('BOT_USERNAME', 'YourBot').lstrip('@')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

app = Client(
    "file_monetization_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_sessions = {}


def get_main_menu_keyboard(is_admin=False):
    """Generate main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 My Statistics", callback_data="menu_stats")],
        [InlineKeyboardButton("📁 My Files & Links", callback_data="menu_files")],
        [InlineKeyboardButton("👥 Referral Program", callback_data="menu_referral")],
        [InlineKeyboardButton("💰 Withdraw Earnings", callback_data="menu_withdraw")],
        [InlineKeyboardButton("📜 Withdrawal History", callback_data="menu_history")],
        [InlineKeyboardButton("ℹ️ Help & Info", callback_data="menu_help")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)


def get_back_button(callback_data="menu_main"):
    """Generate back button keyboard"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data=callback_data)]])


def get_cancel_button(callback_data="cancel"):
    """Generate cancel button keyboard"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=callback_data)]])


def get_admin_keyboard():
    """Generate admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("💵 CPM Management", callback_data="admin_cpm")],
        [InlineKeyboardButton("💸 Withdrawals", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("📺 Ads Management", callback_data="admin_ads")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Check for referral code
    referrer_id = None
    if len(message.command) > 1 and message.command[1].startswith('ref_'):
        try:
            referrer_id = int(message.command[1].replace('ref_', ''))
            if referrer_id == user_id:
                referrer_id = None  # Can't refer yourself
        except:
            pass
    
    get_or_create_user(user_id, username, referrer_id)
    
    if len(message.command) > 1:
        short_link_id = message.command[1]
        file_record = get_file_by_short_link_id(short_link_id)
        
        if file_record:
            try:
                file_type = file_record.get('file_type', 'document')
                caption = f"📁 **{file_record['file_name']}**\n\n✅ Here's your file!"
                
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📊 View My Stats", callback_data="menu_stats")]])
                
                if file_type == 'photo':
                    await message.reply_photo(
                        photo=file_record['telegram_file_id'],
                        caption=caption,
                        reply_markup=keyboard
                    )
                elif file_type == 'video':
                    await message.reply_video(
                        video=file_record['telegram_file_id'],
                        caption=caption,
                        reply_markup=keyboard
                    )
                elif file_type == 'audio':
                    await message.reply_audio(
                        audio=file_record['telegram_file_id'],
                        caption=caption,
                        reply_markup=keyboard
                    )
                else:
                    await message.reply_document(
                        document=file_record['telegram_file_id'],
                        caption=caption,
                        reply_markup=keyboard
                    )
            except Exception as e:
                await message.reply_text(
                    f"❌ Sorry, there was an error retrieving the file.\n\nError: {str(e)}",
                    reply_markup=get_back_button()
                )
        else:
            await message.reply_text(
                "❌ File not found or has expired.",
                reply_markup=get_back_button()
            )
    else:
        cpm_rates = get_cpm_rates()
        welcome_text = f"""
👋 **Welcome to File Monetization Bot!**

📤 **How it works:**
1. Send me any file (document, video, photo, etc.)
2. I'll give you a unique monetized link
3. Share the link with others
4. Earn money for every download! 💰

💵 **Current CPM Rates:**
🇺🇸 US: ${cpm_rates.get('US', 5.0)} per 1000 views
🇬🇧 UK: ${cpm_rates.get('GB', 4.0)} per 1000 views
🇮🇳 India: ${cpm_rates.get('IN', 2.0)} per 1000 views
🌍 Other: ${cpm_rates.get('OTHER', 1.0)} per 1000 views

Start earning now by uploading a file or use the menu below! 🚀
"""
        is_admin = user_id == ADMIN_ID
        await message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(is_admin))


@app.on_message(filters.command("menu"))
async def menu_handler(client: Client, message: Message):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID
    await message.reply_text(
        "📋 **Main Menu**\n\nChoose an option below:",
        reply_markup=get_main_menu_keyboard(is_admin)
    )


@app.on_message(filters.document | filters.video | filters.photo | filters.audio)
async def file_handler(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    get_or_create_user(user_id, username)
    
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "document"
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
        file_type = "video"
    elif message.photo:
        file_id = message.photo.file_id
        file_name = "photo.jpg"
        file_type = "photo"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio.mp3"
        file_type = "audio"
    else:
        await message.reply_text(
            "❌ Unsupported file type.",
            reply_markup=get_back_button()
        )
        return
    
    short_link_id = secrets.token_urlsafe(8)
    short_link = f"{BASE_URL}/download/{short_link_id}"
    
    create_file_record(file_id, file_name, user_id, short_link_id, short_link, file_type)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 View My Stats", callback_data="menu_stats")],
        [InlineKeyboardButton("📤 Upload Another File", callback_data="upload_more")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ])
    
    response_text = f"""
✅ **File Uploaded Successfully!**

📁 **File:** {file_name}
🔗 **Your Monetized Link:**
{short_link}

💰 Share this link and earn money for every view!

**How it works:**
1. Share the link with anyone
2. They go through a secure verification process
3. You earn money based on their location
4. File is delivered automatically

Start sharing now! 🚀
"""
    
    await message.reply_text(response_text, reply_markup=keyboard, disable_web_page_preview=True)


@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    is_admin = user_id == ADMIN_ID
    
    try:
        # Main Menu Navigation
        if data == "menu_main":
            await callback_query.message.edit_text(
                "📋 **Main Menu**\n\nChoose an option below:",
                reply_markup=get_main_menu_keyboard(is_admin)
            )
            await callback_query.answer()
        
        # Statistics
        elif data == "menu_stats":
            stats = get_user_stats(user_id)
            
            if not stats:
                await callback_query.message.edit_text(
                    "📊 **Your Statistics**\n\nNo statistics available yet. Upload a file to get started!",
                    reply_markup=get_back_button()
                )
            else:
                geo_text = ""
                if stats.get('geo_breakdown'):
                    geo_text = "\n\n**📍 Views by Country:**\n"
                    for country, count in sorted(stats['geo_breakdown'].items(), key=lambda x: x[1], reverse=True)[:10]:
                        geo_text += f"• {country}: {count} views\n"
                
                stats_text = f"""
📊 **Your Statistics**

💰 **Balance:** ${stats.get('balance', 0.0):.4f}
👁 **Total Views:** {stats.get('total_views', 0)}
📁 **Files Uploaded:** {stats.get('files_uploaded', 0)}
{geo_text}

Keep sharing your links to earn more! 🚀
"""
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Withdraw", callback_data="menu_withdraw")],
                    [InlineKeyboardButton("🔄 Refresh Stats", callback_data="menu_stats")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
                ])
                await callback_query.message.edit_text(stats_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # Withdraw Menu
        elif data == "menu_withdraw":
            stats = get_user_stats(user_id)
            balance = stats.get('balance', 0) if stats else 0
            
            withdraw_text = f"""
💰 **Withdrawal Request**

**Available Balance:** ${balance:.4f}
**Minimum Amount:** $5.00
**Maximum Amount:** ${balance:.4f}

**Supported Payment Methods:**
• PayPal
• Bank Transfer
• Cryptocurrency (USDT/BTC)

**To request a withdrawal, use:**
/withdraw <amount> <method> <details>

**Examples:**
`/withdraw 10 PayPal yourpaypal@email.com`
`/withdraw 25 Bank 1234567890`
`/withdraw 15 Crypto TRXaddress123`

Your withdrawal will be processed within 24-48 hours.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📜 View History", callback_data="menu_history")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
            ])
            
            if balance < 5.0:
                withdraw_text = f"""
❌ **Insufficient Balance**

**Your current balance:** ${balance:.4f}
**Minimum withdrawal:** $5.00

Keep sharing your links to earn more! 💪
"""
            
            await callback_query.message.edit_text(withdraw_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # Withdrawal History
        elif data == "menu_history":
            withdrawals = get_user_withdrawals(user_id)
            
            if not withdrawals:
                history_text = """
📜 **Withdrawal History**

You haven't made any withdrawal requests yet.

Use the menu below to request your first withdrawal!
"""
            else:
                history_text = "📜 **Withdrawal History**\n\n"
                
                for w in withdrawals[:10]:
                    status_emoji = {
                        'pending': '⏳',
                        'approved': '✅',
                        'rejected': '❌'
                    }.get(w['status'], '❓')
                    
                    history_text += f"""
{status_emoji} **${w['amount']:.2f}** - {w['status'].upper()}
Method: {w['payment_method']}
Date: {w['created_at'].strftime('%Y-%m-%d %H:%M')}
"""
                    if w.get('admin_note'):
                        history_text += f"Note: {w['admin_note']}\n"
                    history_text += "─────────────────\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 New Withdrawal", callback_data="menu_withdraw")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
            ])
            await callback_query.message.edit_text(history_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # Help Menu
        elif data == "menu_help":
            help_text = """
📖 **Help & Information**

**Available Commands:**
• /start - Start the bot & main menu
• /menu - Show main menu
• /withdraw <amount> <method> <details> - Request withdrawal
• /admin - Admin panel (admins only)

**How to Use:**
1️⃣ Send any file to the bot
2️⃣ Receive a monetized link
3️⃣ Share the link
4️⃣ Earn money from downloads
5️⃣ Withdraw earnings when you reach minimum

**Earnings:**
You earn based on visitor's country and our CPM rates.

**Withdrawals:**
• Minimum: $5.00
• Methods: PayPal, Bank, Crypto
• Processing: 24-48 hours

**Support:**
For support, contact the admin.
"""
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💵 View CPM Rates", callback_data="help_cpm")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
            ])
            await callback_query.message.edit_text(help_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # CPM Rates Info
        elif data == "help_cpm":
            cpm_rates = get_cpm_rates()
            cpm_text = "💵 **Current CPM Rates**\n\n"
            
            country_names = {
                'US': '🇺🇸 United States',
                'GB': '🇬🇧 United Kingdom',
                'IN': '🇮🇳 India',
                'OTHER': '🌍 Other Countries'
            }
            
            for code, name in country_names.items():
                rate = cpm_rates.get(code, 1.0)
                cpm_text += f"{name}: ${rate:.2f} per 1000 views\n"
            
            cpm_text += "\n**What is CPM?**\nCPM (Cost Per Mille) is the amount you earn per 1000 views from a specific country."
            
            await callback_query.message.edit_text(cpm_text, reply_markup=get_back_button("menu_help"))
            await callback_query.answer()
        
        # Referral Program
        elif data == "menu_referral":
            ref_stats = get_referral_stats(user_id)
            referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
            
            ref_text = f"""
👥 **Referral Program**

💰 **Your Earnings:**
• Referrals: {ref_stats.get('referral_count', 0)} people
• Earnings: ${ref_stats.get('referral_earnings', 0.0):.4f}

🎁 **Benefits:**
• Get $0.10 for each friend who joins!
• Earn 10% commission on their earnings!
• Unlimited referrals!

🔗 **Your Referral Link:**
`{referral_link}`

**How it works:**
1️⃣ Share your link with friends
2️⃣ They sign up using your link
3️⃣ You earn bonus + 10% of their earnings
4️⃣ Withdraw your earnings anytime!
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Copy Link", url=referral_link)],
                [InlineKeyboardButton("👥 View Referrals", callback_data="view_referrals")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
            ])
            await callback_query.message.edit_text(ref_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # View Referrals List
        elif data == "view_referrals":
            ref_stats = get_referral_stats(user_id)
            referred_users = ref_stats.get('referred_users', [])
            
            if not referred_users:
                ref_list_text = "👥 **Your Referrals**\n\nYou haven't referred anyone yet.\n\nShare your referral link to start earning!"
            else:
                ref_list_text = f"👥 **Your Referrals ({len(referred_users)})**\n\n"
                for idx, ref_user in enumerate(referred_users[:20], 1):
                    username = ref_user.get('username', 'Unknown')
                    joined = ref_user.get('joined_at')
                    date_str = joined.strftime('%Y-%m-%d') if joined else 'N/A'
                    ref_list_text += f"{idx}. @{username} - {date_str}\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Referral", callback_data="menu_referral")],
                [InlineKeyboardButton("📋 Main Menu", callback_data="menu_main")]
            ])
            await callback_query.message.edit_text(ref_list_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # File Manager
        elif data == "menu_files":
            files = get_user_files(user_id, limit=10)
            total_files = get_file_count(user_id)
            
            if not files:
                files_text = """
📁 **My Files & Links**

You haven't uploaded any files yet.

Send me a file to get started!
"""
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Upload File", callback_data="upload_more")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
                ])
            else:
                files_text = f"📁 **My Files & Links** ({total_files} total)\n\n"
                
                keyboard_buttons = []
                for idx, file in enumerate(files, 1):
                    file_name = file.get('file_name', 'Unknown')[:30]
                    views = file.get('views', 0)
                    file_id = str(file.get('_id'))
                    
                    files_text += f"{idx}. **{file_name}**\n"
                    files_text += f"   👁 {views} views\n\n"
                    
                    keyboard_buttons.append([
                        InlineKeyboardButton(f"📊 {file_name[:15]}", callback_data=f"file_view_{file_id}"),
                        InlineKeyboardButton("🗑️", callback_data=f"file_delete_{file_id}")
                    ])
                
                keyboard_buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")])
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await callback_query.message.edit_text(files_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # View File Details
        elif data.startswith("file_view_"):
            file_id = data.replace("file_view_", "")
            file_stats = get_file_stats(file_id)
            
            if not file_stats:
                await callback_query.answer("File not found!", show_alert=True)
                return
            
            geo_text = ""
            if file_stats.get('geo_stats'):
                geo_text = "\n\n**📍 Views by Country:**\n"
                for country, count in sorted(file_stats['geo_stats'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    geo_text += f"• {country}: {count} views\n"
            
            file_detail_text = f"""
📄 **File Details**

**Name:** {file_stats.get('file_name')}
**Views:** {file_stats.get('views', 0)}
**Created:** {file_stats.get('created_at').strftime('%Y-%m-%d') if file_stats.get('created_at') else 'N/A'}
{geo_text}

**Link:** {file_stats.get('short_link')}
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Copy Link", url=file_stats.get('short_link', ''))],
                [InlineKeyboardButton("🗑️ Delete File", callback_data=f"file_delete_{file_id}")],
                [InlineKeyboardButton("🔙 Back to Files", callback_data="menu_files")]
            ])
            await callback_query.message.edit_text(file_detail_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # Delete File Confirmation
        elif data.startswith("file_delete_"):
            file_id = data.replace("file_delete_", "")
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"file_confirm_{file_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="menu_files")]
            ])
            
            await callback_query.message.edit_text(
                "🗑️ **Delete File**\n\nAre you sure you want to delete this file?\nThis action cannot be undone!",
                reply_markup=keyboard
            )
            await callback_query.answer()
        
        # Confirm File Deletion
        elif data.startswith("file_confirm_"):
            file_id = data.replace("file_confirm_", "")
            
            if delete_file(file_id, user_id):
                await callback_query.message.edit_text(
                    "✅ **File Deleted Successfully!**\n\nThe file and its link have been removed.",
                    reply_markup=get_back_button("menu_files")
                )
                await callback_query.answer("File deleted!")
            else:
                await callback_query.message.edit_text(
                    "❌ **Failed to Delete File**\n\nFile not found or you don't have permission.",
                    reply_markup=get_back_button("menu_files")
                )
                await callback_query.answer("Deletion failed!", show_alert=True)
        
        # Upload More
        elif data == "upload_more":
            await callback_query.message.edit_text(
                "📤 **Upload a File**\n\nSend me any file (document, video, photo, audio) to generate a monetized link!",
                reply_markup=get_back_button()
            )
            await callback_query.answer("Send me a file now!")
        
        # Admin Panel
        elif data == "menu_admin":
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            await callback_query.message.edit_text(
                "👨‍💼 **Admin Panel**\n\nChoose an option below:",
                reply_markup=get_admin_keyboard()
            )
            await callback_query.answer()
        
        # Admin Stats
        elif data == "admin_stats":
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            all_stats = get_all_users_stats()
            total_users = len(all_stats)
            total_balance = sum(user.get('balance', 0) for user in all_stats)
            total_views = sum(user.get('total_views', 0) for user in all_stats)
            
            pending_withdrawals = get_pending_withdrawals()
            pending_count = len(pending_withdrawals)
            pending_amount = sum(w.get('amount', 0) for w in pending_withdrawals)
            
            top_users = sorted(all_stats, key=lambda x: x.get('balance', 0), reverse=True)[:5]
            
            top_text = "\n**Top 5 Earners:**\n"
            for idx, user in enumerate(top_users, 1):
                username = user.get('username', 'Unknown')
                balance = user.get('balance', 0)
                top_text += f"{idx}. @{username}: ${balance:.4f}\n"
            
            admin_text = f"""
📈 **System Statistics**

👥 **Total Users:** {total_users}
💰 **Total Payouts:** ${total_balance:.2f}
👁 **Total Views:** {total_views}
⏳ **Pending Withdrawals:** {pending_count} (${pending_amount:.2f})
{top_text}
"""
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
                [InlineKeyboardButton("🔙 Back to Admin", callback_data="menu_admin")]
            ])
            await callback_query.message.edit_text(admin_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # Admin CPM Management
        elif data == "admin_cpm":
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            cpm_rates = get_cpm_rates()
            cpm_text = "💵 **CPM Rate Management**\n\n**Current Rates:**\n\n"
            
            for country, rate in cpm_rates.items():
                cpm_text += f"• {country}: ${rate}\n"
            
            cpm_text += "\n**To update rates, use:**\n`/setcpm <COUNTRY> <RATE>`\n\n**Example:**\n`/setcpm US 6.0`"
            
            await callback_query.message.edit_text(cpm_text, reply_markup=get_back_button("menu_admin"))
            await callback_query.answer()
        
        # Admin Withdrawals
        elif data == "admin_withdrawals":
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            pending = get_pending_withdrawals()
            
            if not pending:
                await callback_query.message.edit_text(
                    "📋 **Pending Withdrawals**\n\nNo pending withdrawal requests.",
                    reply_markup=get_back_button("menu_admin")
                )
            else:
                withdrawals_text = f"📋 **Pending Withdrawals ({len(pending)})**\n\n"
                keyboard_buttons = []
                
                for idx, w in enumerate(pending[:10], 1):
                    withdrawal_id = str(w['_id'])
                    withdrawals_text += f"""
**#{idx} - ID:** `{withdrawal_id[:8]}...`
👤 User: {w['user_id']}
💰 Amount: ${w['amount']:.2f}
💳 Method: {w['payment_method']}
📝 Details: {w['payment_details']}
📅 Date: {w['created_at'].strftime('%Y-%m-%d %H:%M')}
─────────────────────
"""
                    keyboard_buttons.append([
                        InlineKeyboardButton(f"✅ Approve #{idx}", callback_data=f"withdrawal_approve_{withdrawal_id}"),
                        InlineKeyboardButton(f"❌ Reject #{idx}", callback_data=f"withdrawal_reject_{withdrawal_id}")
                    ])
                
                keyboard_buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="admin_withdrawals")])
                keyboard_buttons.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="menu_admin")])
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
                await callback_query.message.edit_text(withdrawals_text, reply_markup=keyboard)
            await callback_query.answer()
        
        # Approve Withdrawal
        elif data.startswith("withdrawal_approve_"):
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            withdrawal_id = data.replace("withdrawal_approve_", "")
            
            # Get withdrawal details before approving
            withdrawal = get_withdrawal_by_id(withdrawal_id)
            
            if withdrawal and approve_withdrawal(withdrawal_id):
                # Send notification to user
                try:
                    user_notification_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 View Stats", callback_data="menu_stats")],
                        [InlineKeyboardButton("📜 View History", callback_data="menu_history")]
                    ])
                    
                    await client.send_message(
                        withdrawal['user_id'],
                        f"""
✅ **Withdrawal Approved!**

Your withdrawal request has been approved!

💰 **Amount:** ${withdrawal['amount']:.2f}
💳 **Method:** {withdrawal['payment_method']}
📝 **Details:** {withdrawal['payment_details']}
📅 **Approved:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

The payment will be processed to your account shortly.

Thank you for using our service! 🎉
""",
                        reply_markup=user_notification_keyboard
                    )
                except Exception as e:
                    print(f"Failed to send notification to user: {e}")
                
                await callback_query.answer("✅ Withdrawal approved!", show_alert=True)
                
                # Refresh the withdrawals list
                pending = get_pending_withdrawals()
                
                if not pending:
                    await callback_query.message.edit_text(
                        "📋 **Pending Withdrawals**\n\n✅ Withdrawal approved successfully!\n\nNo more pending withdrawal requests.",
                        reply_markup=get_back_button("menu_admin")
                    )
                else:
                    withdrawals_text = f"📋 **Pending Withdrawals ({len(pending)})**\n\n✅ Last action: Approved withdrawal\n\n"
                    keyboard_buttons = []
                    
                    for idx, w in enumerate(pending[:10], 1):
                        wid = str(w['_id'])
                        withdrawals_text += f"""
**#{idx} - ID:** `{wid[:8]}...`
👤 User: {w['user_id']}
💰 Amount: ${w['amount']:.2f}
💳 Method: {w['payment_method']}
📝 Details: {w['payment_details']}
📅 Date: {w['created_at'].strftime('%Y-%m-%d %H:%M')}
─────────────────────
"""
                        keyboard_buttons.append([
                            InlineKeyboardButton(f"✅ Approve #{idx}", callback_data=f"withdrawal_approve_{wid}"),
                            InlineKeyboardButton(f"❌ Reject #{idx}", callback_data=f"withdrawal_reject_{wid}")
                        ])
                    
                    keyboard_buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="admin_withdrawals")])
                    keyboard_buttons.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="menu_admin")])
                    keyboard = InlineKeyboardMarkup(keyboard_buttons)
                    await callback_query.message.edit_text(withdrawals_text, reply_markup=keyboard)
            else:
                await callback_query.answer("❌ Failed to approve withdrawal!", show_alert=True)
        
        # Reject Withdrawal
        elif data.startswith("withdrawal_reject_"):
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            withdrawal_id = data.replace("withdrawal_reject_", "")
            
            # Get withdrawal details before rejecting
            withdrawal = get_withdrawal_by_id(withdrawal_id)
            
            if withdrawal and reject_withdrawal(withdrawal_id):
                # Send notification to user
                try:
                    user_notification_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 View Stats", callback_data="menu_stats")],
                        [InlineKeyboardButton("💰 Try Again", callback_data="menu_withdraw")]
                    ])
                    
                    await client.send_message(
                        withdrawal['user_id'],
                        f"""
❌ **Withdrawal Rejected**

Unfortunately, your withdrawal request has been rejected.

💰 **Amount:** ${withdrawal['amount']:.2f}
💳 **Method:** {withdrawal['payment_method']}
📝 **Details:** {withdrawal['payment_details']}
📅 **Processed:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

**Reason:** The withdrawal did not meet our requirements.

Please check your account details and try again. If you have questions, contact support.
""",
                        reply_markup=user_notification_keyboard
                    )
                except Exception as e:
                    print(f"Failed to send notification to user: {e}")
                
                await callback_query.answer("❌ Withdrawal rejected!", show_alert=True)
                
                # Refresh the withdrawals list
                pending = get_pending_withdrawals()
                
                if not pending:
                    await callback_query.message.edit_text(
                        "📋 **Pending Withdrawals**\n\n❌ Withdrawal rejected successfully!\n\nNo more pending withdrawal requests.",
                        reply_markup=get_back_button("menu_admin")
                    )
                else:
                    withdrawals_text = f"📋 **Pending Withdrawals ({len(pending)})**\n\n❌ Last action: Rejected withdrawal\n\n"
                    keyboard_buttons = []
                    
                    for idx, w in enumerate(pending[:10], 1):
                        wid = str(w['_id'])
                        withdrawals_text += f"""
**#{idx} - ID:** `{wid[:8]}...`
👤 User: {w['user_id']}
💰 Amount: ${w['amount']:.2f}
💳 Method: {w['payment_method']}
📝 Details: {w['payment_details']}
📅 Date: {w['created_at'].strftime('%Y-%m-%d %H:%M')}
─────────────────────
"""
                        keyboard_buttons.append([
                            InlineKeyboardButton(f"✅ Approve #{idx}", callback_data=f"withdrawal_approve_{wid}"),
                            InlineKeyboardButton(f"❌ Reject #{idx}", callback_data=f"withdrawal_reject_{wid}")
                        ])
                    
                    keyboard_buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="admin_withdrawals")])
                    keyboard_buttons.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="menu_admin")])
                    keyboard = InlineKeyboardMarkup(keyboard_buttons)
                    await callback_query.message.edit_text(withdrawals_text, reply_markup=keyboard)
            else:
                await callback_query.answer("❌ Failed to reject withdrawal!", show_alert=True)
        
        # Admin Ads Management
        elif data == "admin_ads":
            if user_id != ADMIN_ID:
                await callback_query.answer("❌ Admin only!", show_alert=True)
                return
            
            ad_codes = get_ad_codes()
            
            status_text = "📺 **Ad Codes Management**\n\n"
            ad_types = {
                'popunder': '🔄 Popunder',
                'banner': '📊 Banner',
                'native': '🎯 Native',
                'smartlink': '🔗 Smartlink',
                'social_bar': '📱 Social Bar'
            }
            
            for ad_type, label in ad_types.items():
                code = ad_codes.get(ad_type, '')
                status = "✅ Active" if code else "❌ Not Set"
                status_text += f"{label}: {status}\n"
            
            status_text += "\n**Commands:**\n`/ads set <type>` - Set ad\n`/ads remove <type>` - Remove ad\n\n**Types:** popunder, banner, native, smartlink, social_bar"
            
            await callback_query.message.edit_text(status_text, reply_markup=get_back_button("menu_admin"))
            await callback_query.answer()
        
        # Cancel Operation
        elif data == "cancel":
            if user_id in user_sessions:
                del user_sessions[user_id]
            await callback_query.message.edit_text(
                "❌ **Operation Cancelled**",
                reply_markup=get_back_button()
            )
            await callback_query.answer("Operation cancelled")
        
        else:
            await callback_query.answer("Unknown action")
    
    except Exception as e:
        print(f"Callback error: {e}")
        await callback_query.answer("An error occurred", show_alert=True)


# Legacy command handlers for backward compatibility
@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await message.reply_text(
        "📖 **Help & Information**\n\nUse the menu below to navigate:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ℹ️ Open Help", callback_data="menu_help")]])
    )


@app.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    await message.reply_text(
        "📊 **Your Statistics**\n\nClick below to view your stats:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 View Stats", callback_data="menu_stats")]])
    )


@app.on_message(filters.command("admin"))
async def admin_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.reply_text("❌ This command is only available to administrators.")
        return
    
    await message.reply_text(
        "👨‍💼 **Admin Panel**\n\nAccess admin features below:",
        reply_markup=get_admin_keyboard()
    )


@app.on_message(filters.command("setcpm"))
async def setcpm_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.reply_text(
            "❌ This command is only available to administrators.",
            reply_markup=get_back_button()
        )
        return
    
    if len(message.command) < 3:
        await message.reply_text(
            "❌ **Invalid Format**\n\nUsage: `/setcpm <COUNTRY> <RATE>`\n\nExample: `/setcpm US 6.0`",
            reply_markup=get_back_button("menu_admin")
        )
        return
    
    try:
        country = message.command[1].upper()
        rate = float(message.command[2])
        
        current_rates = get_cpm_rates()
        current_rates[country] = rate
        update_cpm_rates(current_rates)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 View All Rates", callback_data="admin_cpm")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="menu_admin")]
        ])
        await message.reply_text(
            f"✅ **CPM Updated!**\n\nCPM rate for {country} updated to ${rate}",
            reply_markup=keyboard
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid rate. Please provide a number.",
            reply_markup=get_back_button("menu_admin")
        )
    except Exception as e:
        await message.reply_text(
            f"❌ Error updating CPM: {str(e)}",
            reply_markup=get_back_button("menu_admin")
        )


@app.on_message(filters.command("withdraw"))
async def withdraw_handler(client: Client, message: Message):
    user_id = message.from_user.id
    stats = get_user_stats(user_id)
    
    balance = stats.get('balance', 0) if stats else 0
    
    if len(message.command) >= 4:
        try:
            amount = float(message.command[1])
            method = message.command[2]
            details = ' '.join(message.command[3:])
            
            if amount < 5.0:
                await message.reply_text(
                    "❌ Minimum withdrawal amount is $5.00",
                    reply_markup=get_back_button()
                )
                return
            
            if amount > balance:
                await message.reply_text(
                    f"❌ Insufficient balance. You have ${balance:.4f}",
                    reply_markup=get_back_button()
                )
                return
            
            withdrawal = create_withdrawal_request(user_id, amount, method, details)
            
            if withdrawal:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📜 View History", callback_data="menu_history")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
                ])
                
                await message.reply_text(
                    f"""
✅ **Withdrawal Request Submitted!**

**Amount:** ${amount:.2f}
**Method:** {method}
**Status:** Pending Admin Approval

Your request will be processed within 24-48 hours.
You will be notified once it's approved.
""",
                    reply_markup=keyboard
                )
                
                try:
                    await client.send_message(
                        ADMIN_ID,
                        f"""
🔔 **New Withdrawal Request**

User ID: {user_id}
Amount: ${amount:.2f}
Method: {method}
Details: {details}

Use /withdrawals to manage requests.
"""
                    )
                except:
                    pass
            else:
                await message.reply_text(
                    "❌ Failed to create withdrawal request. Please try again.",
                    reply_markup=get_back_button()
                )
        except ValueError:
            await message.reply_text(
                "❌ Invalid amount. Please enter a valid number.",
                reply_markup=get_back_button()
            )
        except Exception as e:
            await message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=get_back_button()
            )
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💰 Withdrawal Info", callback_data="menu_withdraw")]])
        await message.reply_text(
            "💰 **Withdrawal**\n\nClick below for withdrawal information and instructions:",
            reply_markup=keyboard
        )


@app.on_message(filters.command("history"))
async def history_command(client: Client, message: Message):
    await message.reply_text(
        "📜 **Withdrawal History**\n\nClick below to view your history:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📜 View History", callback_data="menu_history")]])
    )


@app.on_message(filters.command("withdrawals"))
async def withdrawals_admin_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.reply_text(
            "❌ This command is only available to administrators.",
            reply_markup=get_back_button()
        )
        return
    
    if len(message.command) >= 3:
        action = message.command[1].lower()
        withdrawal_id = message.command[2]
        note = ' '.join(message.command[3:]) if len(message.command) > 3 else None
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💸 View Withdrawals", callback_data="admin_withdrawals")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin")]
        ])
        
        if action == 'approve':
            if approve_withdrawal(withdrawal_id, note):
                await message.reply_text(
                    f"✅ Withdrawal {withdrawal_id} approved!",
                    reply_markup=keyboard
                )
            else:
                await message.reply_text(
                    "❌ Failed to approve withdrawal.",
                    reply_markup=keyboard
                )
        elif action == 'reject':
            if reject_withdrawal(withdrawal_id, note):
                await message.reply_text(
                    f"❌ Withdrawal {withdrawal_id} rejected!",
                    reply_markup=keyboard
                )
            else:
                await message.reply_text(
                    "❌ Failed to reject withdrawal.",
                    reply_markup=keyboard
                )
        else:
            await message.reply_text(
                "❌ Invalid action. Use: approve or reject",
                reply_markup=keyboard
            )
        return
    
    await message.reply_text(
        "💸 **Withdrawal Management**\n\nClick below to view pending withdrawals:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 View Withdrawals", callback_data="admin_withdrawals")]])
    )


@app.on_message(filters.command("ads"))
async def ads_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.reply_text(
            "❌ This command is only available to administrators.",
            reply_markup=get_back_button()
        )
        return
    
    if len(message.command) >= 2:
        action = message.command[1].lower()
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📺 View Ads", callback_data="admin_ads")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin")]
        ])
        
        if action == "view":
            ad_codes = get_ad_codes()
            
            status_text = "📺 **Current Ad Codes Status**\n\n"
            ad_types = {
                'popunder': '🔄 Popunder',
                'banner': '📊 Banner',
                'native': '🎯 Native Banner',
                'smartlink': '🔗 Smartlink',
                'social_bar': '📱 Social Bar'
            }
            
            for ad_type, label in ad_types.items():
                code = ad_codes.get(ad_type, '')
                status = "✅ Active" if code else "❌ Not Set"
                preview = code[:50] + "..." if len(code) > 50 else code
                status_text += f"{label}: {status}\n"
                if code:
                    status_text += f"  Preview: `{preview}`\n"
                status_text += "\n"
            
            await message.reply_text(status_text, reply_markup=keyboard)
            return
        
        elif action == "set" and len(message.command) >= 3:
            ad_type = message.command[2].lower()
            
            valid_types = ['popunder', 'banner', 'native', 'smartlink', 'social_bar']
            if ad_type not in valid_types:
                await message.reply_text(
                    f"❌ Invalid ad type. Valid types: {', '.join(valid_types)}",
                    reply_markup=keyboard
                )
                return
            
            user_sessions[user_id] = {'action': 'set_ad', 'ad_type': ad_type}
            
            cancel_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            
            await message.reply_text(
                f"""
✏️ **Setting {ad_type.upper()} Ad Code**

Please send your complete Adsterra ad code in the next message.

**Example:**
```html
<script type="text/javascript">
    atOptions = {{
        'key' : 'your-key-here',
        'format' : 'iframe'
    }};
</script>
```

Just paste your complete ad code.
""",
                reply_markup=cancel_keyboard
            )
            return
        
        elif action == "remove" and len(message.command) >= 3:
            ad_type = message.command[2].lower()
            
            if remove_ad_code(ad_type):
                await message.reply_text(
                    f"✅ {ad_type.upper()} ad code removed successfully!",
                    reply_markup=keyboard
                )
            else:
                await message.reply_text(
                    "❌ Failed to remove ad code.",
                    reply_markup=keyboard
                )
            return
    
    await message.reply_text(
        "📺 **Ad Management**\n\nClick below to manage ads:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📺 Manage Ads", callback_data="admin_ads")]])
    )


@app.on_message(filters.text & filters.private & ~filters.command(""))
async def text_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        
        if session.get('action') == 'set_ad':
            ad_type = session.get('ad_type')
            ad_code = message.text
            
            if update_ad_code(ad_type, ad_code):
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📺 View Ads", callback_data="admin_ads")],
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin")]
                ])
                
                await message.reply_text(
                    f"""
✅ **{ad_type.upper()} Ad Code Updated!**

Your ad code has been saved and will now appear on all redirect pages.
""",
                    reply_markup=keyboard
                )
                del user_sessions[user_id]
            else:
                await message.reply_text(
                    "❌ Failed to update ad code. Please try again.",
                    reply_markup=get_cancel_button()
                )


def run_bot():
    print("🤖 Starting Telegram Bot...")
    app.run()


if __name__ == "__main__":
    run_bot()
