from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [KeyboardButton("🔍 View Jobs"), KeyboardButton("👤 My Account")],
        [KeyboardButton("📊 My Stats"), KeyboardButton("💡 Share Bot")],
        [KeyboardButton("⚙️ Change Preferences"), KeyboardButton("☕ Support Us")],
        [KeyboardButton("ℹ️ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_job_type_keyboard():
    """Job type selection"""
    keyboard = [
        [InlineKeyboardButton("💼 Job", callback_data="jtype_Job")],
        [InlineKeyboardButton("🎓 Internship", callback_data="jtype_Internship")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_work_mode_keyboard():
    """Work mode selection"""
    keyboard = [
        [InlineKeyboardButton("🏠 Remote", callback_data="wmode_Remote")],
        [InlineKeyboardButton("🏢 Onsite", callback_data="wmode_Onsite")],
        [InlineKeyboardButton("🔄 Hybrid", callback_data="wmode_Hybrid")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_domains_keyboard(selected=None):
    """Domain selection keyboard"""
    selected = selected or []
    domains = [
        'Python Developer', 'Web Development', 'Data Science',
        'Machine Learning', 'Android Development', 'iOS Development',
        'DevOps', 'Digital Marketing', 'UI/UX Design', 'Content Writing'
    ]
    
    keyboard = []
    for domain in domains:
        check = "✅ " if domain in selected else ""
        keyboard.append([InlineKeyboardButton(
            f"{check}{domain}",
            callback_data=f"domain_{domain}"
        )])
    
    # Add Done button if at least 1 domain selected
    if selected:
        keyboard.append([InlineKeyboardButton("✔️ Done (Selected: {})".format(len(selected)), 
                                              callback_data="domain_done")])
    
    return InlineKeyboardMarkup(keyboard)

def get_job_actions_keyboard(job_url):
    """Actions for each job"""
    keyboard = [
        [InlineKeyboardButton("🔗 View Details", url=job_url)],
        [InlineKeyboardButton("➡️ Next Job", callback_data="next_job"),
         InlineKeyboardButton("❌ Close", callback_data="close_job")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_account_keyboard():
    """Account management keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 My Preferences", callback_data="show_prefs")],
        [InlineKeyboardButton("🔄 Update Preferences", callback_data="update_prefs")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channels_keyboard(channels):
    """Check channels keyboard with friendly names"""
    import config
    keyboard = []
    
    # Use URLs from config if available, otherwise generate generic ones
    for idx, channel_id in enumerate(channels, 1):
        # Check if custom URL is provided
        if config.CHANNEL_URLS and idx <= len(config.CHANNEL_URLS):
            channel_link = config.CHANNEL_URLS[idx - 1]
        else:
            # Generate a generic Telegram link
            # For private channels, this won't work, but it's better than nothing
            channel_link = f"https://t.me/joinchat/placeholder"
        
        keyboard.append([InlineKeyboardButton(
            f"📢 Join Channel {idx}",
            url=channel_link
        )])
    
    keyboard.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data="check_membership")])
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(yes_callback, no_callback):
    """Generic yes/no keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data=yes_callback),
         InlineKeyboardButton("❌ No", callback_data=no_callback)]
    ]
    return InlineKeyboardMarkup(keyboard)
