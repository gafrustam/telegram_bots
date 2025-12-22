import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from game_logic import GameSession

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class BotContext:
    def __init__(self):
        self.sessions = {}
        # Stores list of message IDs to delete for cleanup
        self.cleanup_messages = {} 
        # Map user_id to current job for cancellation
        self.user_jobs = {} 

bot_context = BotContext()

async def clean_chat(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Deletes all tracked messages for the chat."""
    if chat_id in bot_context.cleanup_messages:
        for msg_id in bot_context.cleanup_messages[chat_id]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass # Message likely already deleted or too old
        bot_context.cleanup_messages[chat_id] = []

async def add_cleanup_msg(chat_id, msg_id):
    if chat_id not in bot_context.cleanup_messages:
        bot_context.cleanup_messages[chat_id] = []
    bot_context.cleanup_messages[chat_id].append(msg_id)

async def cancel_user_job(user_id):
    if user_id in bot_context.user_jobs:
        job = bot_context.user_jobs[user_id]
        job.schedule_removal()
        del bot_context.user_jobs[user_id]
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Reset session
    bot_context.sessions[user_id] = GameSession()
    session = bot_context.sessions[user_id]
    
    await clean_chat(chat_id, context)
    
    intro_text = (
        "🧠 *Memory Game* 🧠\n\n"
        "**Rules:**\n"
        "• 8 Rounds per Level.\n"
        "• 3 Hearts ❤️❤️❤️.\n"
        "• **Do NOT type** while digits are shown!\n"
        "• Wait for them to disappear.\n"
        "• Early typing = -1 Heart + Warning.\n"
        "• Levels get harder (faster).\n\n"
        "Good luck!"
    )
    
    msg = await update.message.reply_text(intro_text, parse_mode='Markdown')
    # Do NOT add to cleanup_messages as requested
    
    # Show Pre-Round Menu immediately
    await show_pre_round_menu(chat_id, context, session)

async def show_pre_round_menu(chat_id, context, session, message_text=None):
    """Shows the menu to start next round or change level."""
    # Recalculate time just to show it
    current_time = session.get_time_for_level(session.level)
    
    text = (
        f"{'❤️ ' * session.hearts}\n"
        f"**Level {session.level}** | Round {session.round}/{session.max_rounds}\n"
        f"Time to show: {current_time}s\n"
    )
    
    if message_text:
        text = message_text + "\n\n" + text
        
    buttons = []
    if session.level > 1:
        buttons.append(InlineKeyboardButton("<< Prev Lvl", callback_data='lvl_down'))
        
    buttons.append(InlineKeyboardButton("Run the Level", callback_data='start_round'))
    
    # Always allow leveling up for now, or cap at say 30?
    buttons.append(InlineKeyboardButton("Skip Lvl >>", callback_data='lvl_up'))
    
    keyboard = [buttons]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
    await add_cleanup_msg(chat_id, msg.message_id)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    if user_id not in bot_context.sessions:
        bot_context.sessions[user_id] = GameSession()
    
    session = bot_context.sessions[user_id]
    
    # Logic to handle updates
    if query.data == 'start_round':
        await start_round_execution(chat_id, context, session)
        
    elif query.data == 'lvl_up':
        if session.increase_level_manual():
             await clean_chat(chat_id, context)
             await show_pre_round_menu(chat_id, context, session, f"Level Increased to {session.level}")
             
    elif query.data == 'lvl_down':
        if session.reduce_level():
             await clean_chat(chat_id, context)
             await show_pre_round_menu(chat_id, context, session, f"Level Reduced to {session.level}")
        else:
             # Just flash or re-render? Re-rendering is easier for cleanup logic
             await clean_chat(chat_id, context)
             await show_pre_round_menu(chat_id, context, session, "Already at Level 1")

async def check_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id not in bot_context.sessions:
        return
        
    session = bot_context.sessions[user_id]
    user_text = update.message.text
    
    await add_cleanup_msg(chat_id, update.message.message_id)
    
    # Ignore inputs if IDLE (prevents race conditions/double answers)
    if session.state == "IDLE":
        return

    # Early Input Penalty Check
    if session.state == "SHOWING_NUMBER":
        # Cancel the pending deletion job
        job_cancelled = await cancel_user_job(user_id)
        
        session.hearts -= 1
        msg = await update.message.reply_text("🚨 TOO EARLY! Wait for the number to disappear! (-1 Heart 💔)")
        await add_cleanup_msg(chat_id, msg.message_id)
        
        if session.is_game_over():
            await handle_game_over(chat_id, context, session)
        else:
             # Wait 2 seconds and retry/next round
             # Should we retry the same round or skip? 
             # "And after 2 seconds the next round should appear." implies moving on.
             session.state = "IDLE" 
                          
             pass
             
        # Trigger transition
        context.application.create_task(transition_to_next_round_delayed(chat_id, context, session, 2))
        return

    # Check if number
    if not user_text.isdigit():
        msg = await update.message.reply_text("Digits only please.")
        await add_cleanup_msg(chat_id, msg.message_id)
        return

    # Cancel "Time's up" job?
    if user_id in bot_context.user_jobs:
        await cancel_user_job(user_id)
    
    is_correct = session.check_answer(user_text)
    
    if is_correct:
         text = "✅ *Correct!*"
         msg = await update.message.reply_text(text, parse_mode='Markdown')
         await add_cleanup_msg(chat_id, msg.message_id)
         
         status = session.next_round()
         if status == "LEVEL_COMPLETE":
             # Stat message
             # session.level is still the current completed level (e.g. 6)
             # It is NOT incremented yet (advance_level does that later)
             current_level = session.level
             time_limit = session.get_time_for_level(current_level)
             
             hearts_stat = session.get_hearts_stats()
             
             stats = (
                 f"🎉 *Level {current_level} Complete!*\n\n"
                 f"Show up time: {time_limit}s\n"
                 f"Score: {session.level_correct_count}/{session.max_rounds} correct. {hearts_stat}\n"
                 f"Good job! 👍"
             )
             
             # Send stats
             msg = await context.bot.send_message(chat_id=chat_id, text=stats, parse_mode='Markdown')
             
             session.advance_level()
             context.application.create_task(transition_to_menu(chat_id, context, session))
             return
             
    else:
        if session.is_game_over():
            await handle_game_over(chat_id, context, session)
            return
        else:
            text = f"❌ Wrong! Number was {session.target_number}. Hearts: {session.hearts} 💔"
            session.next_round() 
            msg = await update.message.reply_text(text)
            await add_cleanup_msg(chat_id, msg.message_id)
            
    # Transition Logic
    if session.round > 1 and session.round <= session.max_rounds:
        context.application.create_task(transition_to_next_round(chat_id, context, session))
    else:
        if session.round > session.max_rounds:
             # This block handles case where we advanced past limit in Wrong/Penalty path
             time_limit = session.get_time_for_level(session.level)
             hearts_stat = session.get_hearts_stats()
             
             stats = (
                 f"🎉 *Level {session.level} Complete!*\n\n"
                 f"Show up time: {time_limit}s\n"
                 f"Score: {session.level_correct_count}/{session.max_rounds} correct. {hearts_stat}\n"
                 f"Good job! 👍"
             )
             await context.bot.send_message(chat_id=chat_id, text=stats, parse_mode='Markdown')
             
             session.advance_level()
             context.application.create_task(transition_to_menu(chat_id, context, session))
             return

        context.application.create_task(transition_to_menu(chat_id, context, session))

async def transition_to_next_round(chat_id, context, session):
    await asyncio.sleep(1)
    await start_round_execution(chat_id, context, session)

async def transition_to_next_round_delayed(chat_id, context, session, delay):
    await asyncio.sleep(delay)
    if not session.is_game_over():
         if session.state == "SHOWING_NUMBER": # Reset logic
             session.next_round()
         await start_round_execution(chat_id, context, session)

async def handle_game_over(chat_id, context, session):
    text = f"💔 *Game Over!*\nNumber was {session.target_number}.\nRestarting Level 1..."
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
    session.level = 1
    session.round = 1
    session.hearts = 3
    session.level_correct_count = 0
    context.application.create_task(transition_to_menu(chat_id, context, session))

async def transition_to_menu(chat_id, context, session):
    await asyncio.sleep(1)
    await clean_chat(chat_id, context)
    await show_pre_round_menu(chat_id, context, session)

async def start_round_execution(chat_id, context, session):
    await clean_chat(chat_id, context)
    target_number, time_limit = session.start_new_round()
    
    hearts_str = "❤️ " * session.hearts
    formatted_number = session.get_formatted_number()
    
    text = (
        f"{hearts_str}\n"
        f"Level {session.level} | Round {session.round}/{session.max_rounds}\n\n"
        f"{formatted_number}\n\n"
        f"👀 Memorize it!"
    )
    
    msg = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
    await add_cleanup_msg(chat_id, msg.message_id) # Track it to delete later (next round)
    
    user_id = next((uid for uid, s in bot_context.sessions.items() if s == session), None)
    
    job = context.job_queue.run_once(
        edit_message_job, 
        time_limit, 
        chat_id=chat_id, 
        data={'msg_id': msg.message_id, 'user_id': user_id, 'level': session.level, 'round': session.round, 'hearts': session.hearts}
    )
    if user_id:
        bot_context.user_jobs[user_id] = job

async def edit_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    chat_id = job.chat_id
    
    # Edit message to hide number
    # Reconstruct text
    hearts_str = "❤️ " * data['hearts']
    
    text = (
        f"{hearts_str}\n"
        f"Level {data['level']} | Round {data['round']}/8\n\n"
        f"✨ ****** ✨\n\n"
        f"⏰ *Time's up! Enter the number:*"
    )

    try:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=data['msg_id'], text=text, parse_mode='Markdown')
    except Exception:
        # If edit fails (deleted?), try sending new
        msg = await context.bot.send_message(chat_id=chat_id, text="Time's up! Enter the number:")
        await add_cleanup_msg(chat_id, msg.message_id)
        
    # Update State
    user_id = data['user_id']
    if user_id and user_id in bot_context.user_jobs:
        del bot_context.user_jobs[user_id]
        
    if user_id and user_id in bot_context.sessions:
        bot_context.sessions[user_id].state = "WAITING_INPUT"

if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')
    if not token or token == 'your_token_here':
        print("Error: BOT_TOKEN not set in .env")
        exit(1)
        
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_input))
    
    print("Bot is running...")
    application.run_polling()
