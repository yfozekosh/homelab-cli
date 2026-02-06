from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu() -> InlineKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status_refresh")],
        [InlineKeyboardButton("🖥️ Servers", callback_data="servers")],
        [InlineKeyboardButton("🔌 Plugs", callback_data="plugs")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]])

def get_back_button(callback_data: str = "menu") -> InlineKeyboardButton:
    return InlineKeyboardButton("⬅️ Back", callback_data=callback_data)
