__copyright__ = '© Copyright Ksarp Bots 2021'

import re
import time
import sqlite3
import telebot
import logging
import requests
import wikipedia
import traceback
from bs4 import BeautifulSoup
from gtts import gTTS
from telebot import types
from googletrans import Translator
from deep_translator import GoogleTranslator
from wikipedia.exceptions import DisambiguationError


con = sqlite3.connect("tr_new.db", check_same_thread=False) # подключаемся к базе данных
cur = con.cursor() # создаем объект-курсор

# enable logger
logging.basicConfig(
format='%(asctime)s %(levelname)s: %(message)s',
filename='info.log', filemode='w',
level=logging.DEBUG)

TOKEN = '1821952294:AAERWo295ydLbstgWYxch4PJr9kJfm7VkBY' # это токен моего бота
bot = telebot.TeleBot(TOKEN, parse_mode='Markdown')

admin_id = [1785108916, 5347145575]  # admin's id
down_s = 'Перевожу🔄'
msg_ids = {}
post_message = []
post_buttons = []


class Datas:
    def __init__(self, message):
        self.u_id = message.from_user.id
        self.f_name = message.from_user.first_name
        self.u_name = message.from_user.username

    
def validation(u_id: int) -> bool:
    status = ['creator', 'administrator', 'member']
    check = bot.get_chat_member('@Ksarp_bots', u_id).status
    
    if check not in status:
        return True
    else:
        return False


def all_users() -> list:
    arr = cur.execute("SELECT * FROM users").fetchall()
    return arr


def post_settings():
    buttons = [
        types.InlineKeyboardButton(text='Add button', callback_data='add_b'),
        types.InlineKeyboardButton(text='Add message', callback_data='add_m'),        
        types.InlineKeyboardButton(text='Show message', callback_data='show_m'),
        types.InlineKeyboardButton(text='Reset all!', callback_data='reset_all')
    ]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    
    return markup


def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Back', callback_data='back'))
    return markup


def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Выбрать язык🌏', 'Помощь⁉')
    markup.row('Про бота💬', 'Отзывы📫️')
    markup.add('Wikipedia🌐')

    return markup


@bot.message_handler(commands=['start'])
def start(message):
    data = Datas(message)
    if validation(message.from_user.id):

        bot.send_message(message.from_user.id, '*Пожалуйста подпишитесь на канал @Ksarp_bots*')
        return False;
    
    result = cur.execute(f"""SELECT * FROM users WHERE id = ?""", (data.u_id,)).fetchall()       

    if result == None or result == [] or result == ():      # Регистрируем пользователя
        cur.execute(f"""
        INSERT INTO users (id, username, name, lang, trans) VALUES (?, ?, ?, ?, ?)
        """, (data.u_id, data.u_name, data.f_name, 'ru', 'hello',))
        con.commit()
    else:
        pass
        
    bot.reply_to(message, f'''
*Привет {data.f_name},
это обычный бот переводчик🤖.
Если не поняли как использовать
нажмите на /help*''', reply_markup=main_keyboard())


@bot.message_handler(commands=['help'])
def help1(message):
    text = """
*Использования бота:
нажмите на кнопку снизу Выбрать язык
и выберите для вас подходящий язык а потом
введите текст*
"""
    bot.reply_to(message, text)


@bot.message_handler(regexp='Назад🔙️')
def main_menu(message):
    u_id = message.from_user.id
    u_name = message.from_user.username
    f_name = message.from_user.first_name
    m_id = message.message_id
    status = ['creator', 'administrator', 'member']

    if bot.get_chat_member('@Ksarp_bots', u_id).status not in status:
        bot.reply_to(message, '*Пожалуйста подпишитесь на канал @Ksarp_bots*')
        return False;
    else:
        m_id = message.message_id
        
        bot.reply_to(message, "*меню🔝*", reply_markup=main_keyboard())


@bot.message_handler(regexp='Wikipedia🌐')
def wiki1(message):
    u_id = message.from_user.id
    u_name = message.from_user.username
    f_name = message.from_user.first_name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Назад🔙️')

    status = ['creator', 'administrator', 'member']

    if bot.get_chat_member('@Ksarp_bots', u_id).status not in status:
        bot.reply_to(message, '*Пожалуйста подпишитесь на канал @Ksarp_bots*')
        return False;
    else:
        count = 0
        text = bot.reply_to(message, '*Wikipedia🌐*\n\n_введите ваш запрос:_',
        reply_markup=markup)
        
        bot.register_next_step_handler(text, wiki_main)
        

def wiki_main(message):
    u_id = message.from_user.id
    if message.text == 'Назад🔙️': return main_menu(message)
    try:    
        msg = bot.reply_to(message, 'Подождите...')
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='RUS', callback_data='ru_wiki'))
        wikipedia.set_lang('en')
        page2 = wikipedia.page(message.text)
        page_url = page2.url
        page_text = wikipedia.summary(message.text, sentences=2000)
        
        bot.reply_to(message, page_text, reply_markup=keyboard)
        bot.delete_message(message.from_user.id, msg.message_id)
        return main_menu(message)
    except Exception as e:
        bot.send_message(u_id, f'По запросу `{message.text}` ничего не найдено ✖️', reply_markup=main_keyboard())           
        bot.send_message(admin_id, e)               
        print(traceback.print_exc())
        return                   
    except DisambiguationError as dis_err:
        bot.reply_to(message, dis_err, reply_markup=main_keyboard())
    except IndexError as e:
        print(e)


@bot.callback_query_handler(func=lambda c: c.data == 'ru_wiki')
def tr_wiki(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    call_id = call.from_user.id
    call_text = call.message.text
    translated_text = GoogleTranslator(source='auto', target='ru').translate(call_text)
    
    bot.edit_message_text(
        chat_id=call_id,
        message_id=call.message.message_id,
        text=translated_text
    )


@bot.message_handler(regexp='Выбрать язык🌏')
def lang(message):
    u_id = message.from_user.id
    u_name = message.from_user.username
    f_name = message.from_user.first_name
    status = ['creator', 'administrator', 'member']

    if bot.get_chat_member('@Ksarp_bots', u_id).status not in status:
        bot.send_message(u_id, '*Пожалуйста подпишитесь на канал @Ksarp_bots*')
        return False;
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('ENG🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'RUS🇷🇺')
        keyboard.add('UZB🇺🇿')
        keyboard.add('Назад🔙️')
        
        bot.delete_message(u_id, message.message_id)
        bot.send_message(message.chat.id, '*Выберите язык для перевода🔧*', reply_markup=keyboard)


@bot.message_handler(regexp='Помощь⁉')
def helper(message):
    u_id = message.from_user.id
    u_name = message.from_user.username
    f_name = message.from_user.first_name
    status = ['creator', 'administrator', 'member']

    if bot.get_chat_member('@Ksarp_bots', u_id).status not in status:
        bot.reply_to(message, '*Пожалуйста подпишитесь на канал @Ksarp_bots*')
        return False
    else:
        bot.reply_to(message,'''
Чтобы начать работу
нажмите на кнопку *Выбрать язык🌏*
а потом выберите нужный для вас язык''',
)


@bot.message_handler(regexp='Про бота💬')
def info(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, """
*Этот бот переводчик поддерживает 
три языка и +озвучка текста,
присоединяйтесь в наш канал @Ksarp_bots
чтобы узнавать новости*""")


@bot.message_handler(regexp='Отзывы📫️')
def msg_users(message):
    u_id = message.from_user.id
    u_name = message.from_user.username
    f_name = message.from_user.first_name
    status = ['creator', 'administrator', 'member']

    if bot.get_chat_member('@Ksarp_bots', u_id).status not in status:
        bot.reply_to(message, 'Пожалуйста подпишитесь на канал @Ksarp_bots')
        return False;
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Назад🔙️')
        chat_id = message.chat.id
        bsm = bot.reply_to(message, "_Пишите ваш отзыв:_", reply_markup=markup)
        bot.register_next_step_handler(bsm, database)


def database(message):
    data = Datas(message)
    if message.text == 'Назад🔙️': return main_menu(message)

    for admin in admin_id:
        bot.send_message(
    admin, f"""
*🆔:* `{data.u_id}`
*От:* [{data.f_name}](t.me/{data.u_name})
*Отзыв:* `{message.text}`
""")
    
    bot.send_message(data.u_id, "*Ваш отзыв принят📩️*", reply_markup=main_keyboard())
    return


@bot.message_handler(regexp='.nodir')
def check(message):
    data = Datas(message)   
    if data.u_id in admin_id:
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('📊Statistika', '/start')
        markup.add('send_message📩', 'Отправить сообщения всем!')
        
        bot.send_message(data.u_id, f"""
👋Привет, [создатель](t.me/nodir_404)
🆔: {data.u_id}""", reply_markup=markup)
    else:
        bot.send_message(data.u_id, '*Ты кто такой? давай до свидания)*')


@bot.message_handler(regexp='📊Statistika')
def Statistika(message):
    u_id = message.from_user.id
    
    if u_id in admin_id:
        cur.execute("SELECT * FROM users")
        arr = cur.fetchall()
        quantity_u = len(arr) 
        
        ar_txt = []
        bot.send_message(message.from_user.id, f'''
*👦Users: {quantity_u}*
''')

        for data in arr:    
            ar_txt.append(f"id: {data[0]}\nusername: @{data[1]}\nname: {data[2]}")
            
        with open('users.txt', 'w', encoding="utf-8") as f:
            f.write('\n\n'.join(ar_txt))
        
        file = open('users.txt', 'r', encoding='utf-8')
        bot.send_document(u_id, file)
        file.close()
    else:
        bot.send_message(u_id, '*Вы не админ!*')
        

@bot.message_handler(regexp='send_message📩')
def sender(message):
    if message.from_user.id in admin_id:
        text = bot.send_message(message.from_user.id, '''
*Отправьте сообщения в таком формате:*
<id> <message>
''')
        bot.register_next_step_handler(text, sender_main)
    else:
        return False


def sender_main(message):
    try:    
        text_d = message.text.split(' ')
        text = ' '.join(text_d[1:])
        u_id = text_d[0]
        bot.send_message(int(u_id), f'*Сообщения:\n{text}*')
        bot.send_message(message.from_user.id, 'Succes!')
    except Exception as e:
        bot.send_message(message.from_user.id, f'`{e}`')


@bot.message_handler(regexp='Отправить сообщения всем!')
def send_for_all(message):
    u_id = message.from_user.id
    
    if u_id in admin_id:
        bot.reply_to(message, 'Choose:', reply_markup=post_settings())
    else:
        bot.reply_to(message, "Иди нахуй!")


@bot.callback_query_handler(func=lambda c: c.data == 'add_m')
def add_message(call):
    msg = bot.send_message(1785108916, 'Send me a message which u want send to users:')
    msg_ids['add_m_id'] = msg.message_id
    bot.register_next_step_handler(msg, add_message2)


def add_message2(msg):
    bot.delete_message(msg.from_user.id, msg_ids.get('add_m_id'))
    m_id = msg.message_id
    post_message.append(m_id)
    bot.send_message(1785108916, 'Saved!')
    

@bot.callback_query_handler(func=lambda c: c.data == 'add_b')
def set_b(call):
    bot.answer_callback_query(call.id)
    call_id = call.from_user.id
    msg = bot.send_message(call_id, "Enter a link:")
    bot.register_next_step_handler(msg, set_b2)


def set_b2(message):
    u_id = message.from_user.id
    n_a_l = message.text.split(':')
    print(n_a_l)
    post_buttons.append(types.InlineKeyboardButton(text=n_a_l[0], url=n_a_l[1] + ":" + n_a_l[2]))
    
    bot.send_message(u_id, 'added!', reply_markup=post_settings())


@bot.callback_query_handler(func=lambda c: c.data == 'show_m')
def show_m(call):
    bot.answer_callback_query(call.id)
    call_id = call.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(*post_buttons)
    markup.add(types.InlineKeyboardButton(text='Send', callback_data='send_m'))
    bot.copy_message(call_id, admin_id[0], post_message[0], reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == 'back')
def back(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, 'menu', reply_markup=main_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == 'reset_all')
def res_all(call):
    call_id = call.from_user.id
    bot.answer_callback_query(call.id)
    post_buttons.clear()
    post_text.clear()
    
    bot.edit_message_text(
        chat_id=call_id,
        message_id=call.message.message_id,
        text='Succes!',
        reply_markup=post_settings() # reply markup) 
    )
    return # Safety exit from func


@bot.callback_query_handler(func=lambda c: c.data == 'send_m')
def send_to_everyone(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*post_buttons)
    good = 0
    bad = 0

    for user in all_users():
        try:
            bot.copy_message(user[0], admin_id[0], post_message[0], reply_markup=markup)    
            good += 1
        except Exception as e:
            print(e)
            bad += 1
            continue

    bot.send_message(call.from_user.id, f"Sent: {good}\nDon't sent: {bad}")


@bot.message_handler(content_types=['text'])
def parser(message):
    data = Datas(message)
    status = ['creator', 'administrator', 'member']
    msg = None

    if bot.get_chat_member('@Ksarp_bots', data.u_id).status not in status:
        bot.reply_to(message, '*Пожалуйста подпишитесь на канал @Ksarp_bots*')
        return False;
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='озвучить🗣️', callback_data='voice'))
        
        if message.text == 'ENG🏴󠁧󠁢󠁥󠁮󠁧󠁿':
            cur.execute(f"UPDATE users SET lang = ? WHERE id = ?", ('en', data.u_id,))
            con.commit()
            msg = bot.reply_to(message,'''        
*Вы выбрали перевод на Английский язык.
Введите текст:*
''')
        elif message.text == 'RUS🇷🇺':
            cur.execute(f"UPDATE users SET lang = ? WHERE id = ?", ('ru', data.u_id,))
            con.commit()
            msg = bot.reply_to(message,'''        
*Вы выбрали перевод на Русский язык.
Введите текст:*
''')
        elif message.text == 'UZB🇺🇿':
            cur.execute(f"UPDATE users SET lang = ? WHERE id = ?", ('uz', data.u_id,))
            con.commit()
            msg = bot.reply_to(message,'''        
*Вы выбрали перевод на Узбекский язык.
Введите текст:*
''')
        else:
            if msg != None:
                bot.delete_message(message.from_user.id, msg.message_id)
            
            try:
                langu1 = cur.execute(f"SELECT lang FROM users WHERE id = ?", (data.u_id,))
                langu = cur.fetchall()
                tr = Translator()
                tr_text = tr.translate(message.text, src='auto', dest=langu[0][0]).text
                json2 = GoogleTranslator(source='auto', target=langu[0][0]).translate(message.text)

                m = bot.reply_to(message, down_s)
                bot.send_chat_action(message.from_user.id, 'typing')
                m2 = bot.reply_to(message, f"`{tr_text}`", reply_markup=keyboard)
                bot.delete_message(message.from_user.id, m.message_id)
            except Exception as e:
                print('error!', e.with_traceback())
                bot.send_message(data.u_id, '''
*⚠️что-то пошло не так.
Напишите в отзывы что произошло⚠️*''')


@bot.callback_query_handler(func=lambda c: c.data == 'voice')
def converter(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    call_id = callback_query.from_user.id
    try:
        langu1 = cur.execute(f"SELECT lang FROM users WHERE id = ?", (call_id,))
        langu = cur.fetchall()
        text = callback_query.message.text
        speech = gTTS(text=text, lang=langu[0][0], slow=False)
        speech.save('text.ogg')
        audio = open('text.ogg', 'rb')
        bot.send_audio(callback_query.from_user.id, audio)
    except Exception as e:
        print('error with voice')
        text = '''
*⚠️что-то пошло не так.
Напишите в отзывы что произошло⚠*
'''
        bot.send_message(callback_query.from_user.id, text)


if __name__ == '__main__':    
    print('started')
    bot.infinity_polling()

