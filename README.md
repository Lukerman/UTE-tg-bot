# 📁 Telegram File Monetization Bot

A complete Telegram bot system that enables users to upload files and earn money from downloads through a monetized link system with geo-tracking and CPM-based earnings.

## ✨ Features

- 🤖 **Telegram Bot** - Easy file uploads via Telegram
- 💰 **Monetization** - Earn money from every download
- 🌍 **Geo-Tracking** - Country-based CPM rates
- 🔒 **Security** - Token protection, rate limiting, anti-spam
- 📊 **Statistics** - Track views and earnings
- 👨‍💼 **Admin Panel** - Manage CPM rates and view system stats

## 🚀 Quick Start

### Prerequisites

1. **MongoDB Atlas Account** (free)
   - Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Create a cluster and get connection string

2. **Telegram Bot Token**
   - Message [@BotFather](https://t.me/BotFather)
   - Create new bot with `/newbot`

3. **Telegram API Credentials**
   - Visit [my.telegram.org](https://my.telegram.org)
   - Get API_ID and API_HASH

### Setup

1. **Configure Environment Variables**
   
   Add these secrets in Replit:
   ```
   BOT_TOKEN=your_bot_token
   API_ID=your_api_id
   API_HASH=your_api_hash
   MONGO_URI=your_mongodb_connection_string
   BASE_URL=your_repl_url
   BOT_USERNAME=your_bot_username
   ADMIN_ID=your_telegram_user_id
   SECRET_KEY=random_secret_key
   ```

2. **Run the Bot**
   - Click "Run" in Replit
   - Bot and web server will start automatically

3. **Start Using**
   - Open your bot on Telegram
   - Send any file
   - Share the monetized link!

## 📖 How It Works

### Upload Process
1. User sends file to bot
2. Bot generates unique monetized link
3. User shares link

### Download Process
1. Visitor opens link
2. Goes through 4 verification pages (with timers)
3. System tracks location and calculates earnings
4. Visitor gets file from bot
5. Uploader earns money!

## 💵 Default CPM Rates

| Country | Rate per 1000 views |
|---------|---------------------|
| 🇺🇸 US  | $5.00              |
| 🇬🇧 UK  | $4.00              |
| 🇮🇳 India | $2.00            |
| 🌍 Other | $1.00             |

## 🎮 Bot Commands

- `/start` - Start bot / receive file
- `/stats` - View your statistics
- `/help` - Get help
- `/admin` - Admin dashboard (admin only)
- `/setcpm <COUNTRY> <RATE>` - Update CPM (admin only)

## 🛠️ Tech Stack

- **Python 3.11** - Programming language
- **Pyrogram** - Telegram Bot API
- **Flask** - Web framework
- **MongoDB** - Database
- **ipapi.co** - Geo-location service

## 📁 Project Structure

```
├── main.py          # Application entry point
├── bot.py           # Telegram bot logic
├── web.py           # Flask web application
├── database.py      # MongoDB operations
├── requirements.txt # Dependencies
└── .env            # Configuration (create this)
```

## 📚 Documentation

See [replit.md](replit.md) for detailed setup instructions, architecture overview, and troubleshooting guide.

## 🔒 Security

- Token-based URL protection
- Rate limiting (10 req/5min per IP)
- Anti-spam (duplicate view prevention)
- Secure session management

## 📝 License

This project is open source and available for educational purposes.

## 🤝 Support

For issues or questions:
1. Check the [replit.md](replit.md) troubleshooting section
2. Review console logs for errors
3. Contact bot admin

---

**Made with ❤️ for Replit**
