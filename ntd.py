import config
import telebot
import mariadb

ntd = telebot.TeleBot(config.token)


############################# Functions #########################################

def keyboard_main(call1, call2):
    keyboard_main = telebot.types.InlineKeyboardMarkup()
    button_1 = telebot.types.InlineKeyboardButton(text="Назад", callback_data=call1)
    button_2 = telebot.types.InlineKeyboardButton(text="Вперед", callback_data=call2)
    keyboard_main.add(button_1, button_2)
    return keyboard_main

def keyboard_call_massive(resultslist, user_req):
    keyboard_list = []
    call_list = []
    i = 1
    for item in resultslist:
        a = i + 1
        call1 = str(i) + '_' + user_req
        call2 = str(a) + '_' + user_req
        call_list.append(call1)
        call_list.append(call2)
        keyboard_list.append(keyboard_main(call1, call2))
        i += 2
    return keyboard_list, call_list


def search_in_base(mes):
    ntd_req = '%' + mes + '%'
    conn = mariadb.connect(
        user=config.login,
        password=config.passw,
        host=config.hostbase,
        port=config.portbase,
        database="reestr")
    cursor = conn.cursor()
    cursor.execute("SELECT numberN ,name, date_utv, date_vvod, old, inf, date_otm FROM ntd WHERE \
        numberN LIKE ? OR name LIKE ? OR date_utv LIKE ? OR\
        date_vvod LIKE ? OR old LIKE ? OR inf LIKE ? OR date_otm LIKE ?", (ntd_req, ntd_req, ntd_req, ntd_req, ntd_req, ntd_req, ntd_req))
    results = cursor.fetchall()
    # еще есть sql_fetch()
    conn.close()
    resultss_lists = [list(ele) for ele in results]
    return resultss_lists

def one_page (base_answer):
    p = 0
    for row_search in base_answer:
        m = 0
        for col_search in row_search:
            if m == 0:
                col_search = '<b>Обозначение НД: </b>' + '<u>' + col_search + '</u>' + '\n'
                row_search[m] = col_search
            if m == 1:
                col_search = '<b>Наименование НД: </b>' + col_search + '\n'
                row_search[m] = col_search
            if m == 2:
                col_search = '<b>Дата утверждения: </b>' + col_search + '\n'
                row_search[m] = col_search
            if m == 3:
                col_search = '<b>Дата ввода в действие: </b>' + col_search + '\n'
                row_search[m] = col_search
            if m == 4:
                col_search = '<b>Преемственность НД: </b>' + col_search + '\n'
                row_search[m] = col_search
            if m == 5:
                col_search = '<b>Сведения об изменениях: </b>' + col_search + '\n'
                row_search[m] = col_search   
            if m == 6:
                col_search = '<b>Дата отмены действия: </b>' + col_search + ' '
                row_search[m] = col_search
            m += 1
           
        row_search = ''.join(row_search)
        row_search = (row_search + '\n\n' + '<i>' + 'Результат %d из %d' + '</i>') % ((p + 1), (len(base_answer)))
        base_answer[p] = row_search
        p += 1
    return base_answer

############################# Handlers #########################################

@ntd.message_handler(commands=['start'])
def answer_help(message):
    ntd.send_message(message.chat.id, "Данный бот предназначен для поиска актуальной информации о состоянии нормативных документов ОСТ. \n <b>Поиск не зависит от регистра вводимых букв и аналогичен поиску по реестру в файле формата .xls(x) (то есть зависит, например, от падежа).</b> \n Основой базы данных для поиска является реестр нормативно-технической документации (тот самый, распространяемый в экселевском файле .xls(x)). <b>Дату составления и другую информацию о реестре всегда можно посмотреть в описании бота в разделе \"Информация\"</>. \n Для поддержания базы НТД в максимально актуальном состоянии новые реестры в формате .xls(x) можно отправлять на электронную почту tntdbot@yandex.ru. \n\n Для повторного вывода данного сообщения введите /start. \n\n Для начала работы введите поисковый запрос, например, \"037-14\" (без кавычек).", parse_mode='HTML')

@ntd.message_handler(content_types=['audio', 'photo', 'voice', 'video', 'document', 'location', 'contact', 'sticker'])
def answer_help(message):
    ntd.send_message(message.chat.id, "Мне некогда развлекаться, давай по делу!")

@ntd.message_handler(content_types = ["text"])
def answer_text(message):

    results_list = search_in_base(message.text)

    if len(results_list) == 1:
        result = one_page (results_list)
        ntd.send_message(message.chat.id, result[0], parse_mode='HTML')
    
    elif (len(results_list) > 1) and (len(results_list) <= 20):
        result = one_page (results_list)
        keyboard_many, call_many = keyboard_call_massive(result, message.text)
        ntd.send_message(message.chat.id, result[0], parse_mode='HTML', reply_markup = keyboard_many[0])
        
    elif (len(results_list) > 20):
        ntd.send_message(message.chat.id, "Найдено более 20 совпадений. Сократите запрос.")
    
    else:
        ntd.send_message(message.chat.id, "Ничего не найдено.")
       

@ntd.callback_query_handler(func=lambda call: True)
def callback_from_main_button(call):
    call_massive = call.data.split('_')
    call_int = int(call_massive[0])
    call_message = call_massive[1]

    results_list_call = search_in_base(call_message)
    result_call = one_page (results_list_call)
    keyboard_many_call, call_many_call = keyboard_call_massive(result_call, call_message)
    
    if (call_int % 2 != 0) and ((((call_int - 1) /2) - 1) < 0):
        ntd.answer_callback_query(call.id, text='Вы уже на первой странице.')
    elif (call_int % 2 == 0) and ((call_int /2) < len(keyboard_many_call)):
        ntd.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=result_call[int((call_int / 2))], parse_mode='HTML', reply_markup=keyboard_many_call[int((call_int / 2))])
        ntd.answer_callback_query(call.id)
    elif (call_int % 2 != 0) and ((((call_int - 1) /2) - 1) >= 0):
        ntd.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=result_call[int(((call_int - 1) / 2) - 1)], parse_mode='HTML', reply_markup=keyboard_many_call[int(((call_int - 1) / 2) - 1)])
        ntd.answer_callback_query(call.id)
    elif (call_int % 2 == 0) and ((call_int /2) == len(keyboard_many_call)):
        ntd.answer_callback_query(call.id, text='Вы уже на последней странице.')



if __name__ == '__main__':
    ntd.infinity_polling()
