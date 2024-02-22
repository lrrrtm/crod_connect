import json
import os

import psycopg2 as pg
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from docx2pdf import convert as pdf_convert
from docxtpl import DocxTemplate
from psycopg2 import extras

from source.buttons import *
from source.db_requests import *

script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
os.chdir(script_directory)
project_folder = os.getcwd()

with open(f'{project_folder}\config.json', encoding='utf-8') as f:
    config_data = json.load(f)

bot = Bot(token=config_data['bot']['token'], parse_mode="Markdown")
dp = Dispatcher(bot, storage=MemoryStorage())

modules = {}

radio_status = False
radio_flags = []


class Feedback(StatesGroup):
    feedback_text = State()
    feedback_mark = State()


class Radio(StatesGroup):
    request = State()


try:
    db_config = config_data['database']
    connection = pg.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['db_name'],
    )
    cur = connection.cursor(cursor_factory=extras.RealDictCursor)
    print("Connected!")
except Exception as err:
    print("Not connected")


@dp.callback_query_handler()
async def check_callback(callback: types.CallbackQuery):
    print(callback.data)
    user_status, action = callback.data.split("_")[0], callback.data.split("_")[1]
    tID = callback.message.chat.id
    if user_status == "admin":
        if action == "getfeedback":
            modules_list = await get_modules_list()
            mk = types.InlineKeyboardMarkup(row_width=1)
            for module in modules_list:
                mk.add(types.InlineKeyboardButton(text=f"{module['module_name']}",
                                                  callback_data=f"admin_sendfeedback_{module['tutor_id']}"))
            mk.add(types.InlineKeyboardButton(text="Все модули", callback_data=f"admin_sendfeedback_all"))
            await bot.send_message(text="*Выберите модуль для получения обратной связи*", chat_id=tID, reply_markup=mk)
        elif action == "sendfeedback":
            await bot.delete_message(chat_id=tID, message_id=callback.message.message_id)
            module_id = callback.data.split("_")[-1]
            if module_id != "all":
                await send_feedback(module_id, tID)
            else:
                data = await get_modules_list()
                for a in data:
                    await send_feedback(a['tutor_id'], tID)
        elif action == "restart":
            mk = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton(text="Перейти в CROD.CONNECT", url="https://clck.ru/36XFzU"))
            await callback.message.answer(text="*Перезапуск смены осуществляется только через интерфейс CROD.CONNECT*",
                                          reply_markup=mk)
        elif action == "approveradio":
            child_id = callback.data.split("_")[-1]
            await bot.edit_message_text(chat_id=tID, message_id=callback.message.message_id,
                                        text=callback.message.text + "\n\n🟢 *Заявка принята*")
            await bot.send_message(chat_id=child_id,
                                   text="📨*Тук-тук, новое сообщение*\n\n*Твоя заявка на радио обработана, жди в эфире уже совсем скоро!*")
            radio_flags.remove(int(child_id))
        elif action == "declineradio":
            child_id = callback.data.split("_")[-1]
            await bot.edit_message_text(chat_id=tID, message_id=callback.message.message_id,
                                        text=callback.message.text + "\n\n🔴 *Заявка отклонена*")
            await bot.send_message(chat_id=child_id,
                                   text="📨*Тук-тук, новое сообщение*\n\n*К сожалению, твоя заявка отклонена, возможно она не прошла цензуру, но ты можешь отправить новую, пока наше радио в эфире*")
            radio_flags.remove(int(child_id))

    elif user_status == "mentors":
        if action == "childrenlist":
            mentor_group = await get_mentor_group(tID)
            children_list = await get_children_list(filter='group', value=int(mentor_group))
            if len(children_list) != 0:
                text = ""
                for a in range(len(children_list)):
                    text += f"\n{a + 1}. {children_list[a][0]} {children_list[a][1]}"
                await bot.send_message(chat_id=tID, text=text)
            else:
                await callback.answer(text="Список детей вашей группы отсутствует", show_alert=True)

    elif user_status == "tutor":
        module_info = await get_module_info(tID)
        if action == "childrenlist":
            children_list = await get_children_list(filter='modules', value=module_info['tutor_id'])
            if len(children_list) != 0:
                pass
            else:
                await callback.answer("На ваш модуль пока никто не записан", show_alert=True)
        elif action == "getfeedback":
            await send_feedback(tID, tID)

    elif user_status == "children":
        if action == "modules":
            await reg_modules_process(tID)
        elif action == "addmodule":
            avaliable_modules = await get_registered_modules(tID)
            if len(avaliable_modules) < config_data['modules_count']:
                module_id = callback.data.split("_")[-1]
                if module_id not in modules[tID]:
                    if await seats(module_id):
                        # await callback.answer(f"Запись на модуль {module_id} успешна!", show_alert=True)
                        await bot.delete_message(chat_id=tID, message_id=callback.message.message_id)
                        modules[tID].append(module_id)
                        await add_module_to_children(tID, module_id)
                        await reg_modules_process(tID)

                    else:
                        await callback.answer(
                            text="На этом модуле уже не осталось свободных мест, выбери другой модуль",
                            show_alert=True)
                else:
                    await callback.answer(
                        text="Нельзя зарегистрироваться на один модуль несколько раз, выбери другой модуль",
                        show_alert=True)
            else:
                await callback.answer(text="Ты уже записан(-а) на максимально возможное количество модулей",
                                      show_alert=True)

        elif action == "sendfeedback":
            # # получаю из feedback все фидбеки за текущий день от данного ребёнка
            # feedback_list = await get_feedback_by_child(tID)
            # if len(feedback_list) < config_data['modules_count']:
            #     pass
            # # если количество фидбеков меньше, чем количество модулей, то отправляю сообщение с фидбеком по первому модулю
            # # после загрузки первого фидебка снова делаю запрос фидбеков за текущий день
            # # если фидбеков меньше, чем надо, отправляю следующий запрос по модулю, иначе окончание обратки
            # # иначе говорю, что всё уже отправлено
            pass

        elif action == "radio":
            if radio_status:
                if tID not in radio_flags:
                    await bot.delete_message(chat_id=tID, message_id=callback.message.message_id)
                    await Radio.request.set()
                    await bot.send_message(chat_id=tID,
                                           text="*Радио ждёт именно тебя!* \n\nОтправь название песни, чтобы мы включили её на нашем радио "
                                                "или напиши пожелание, которое мы озвучим в прямом эфире! (не забудь указать, "
                                                "кому адресовано пожелание)"
                                                "\n\nЧтобы вернуться назад, отправь /start"
                                                "\n\n_Все заявки проходят проверку на цензуру, поэтому не все песни могут прозвучать в эфире_")
                else:
                    await callback.answer(
                        text="У тебя уже есть активная заявка. Подожди, пока мы её обработаем, чтобы отправить новую",
                        show_alert=True)
            else:
                await callback.answer(
                    text="Сейчас наше радио не работает, как только мы будем в эфире, тебе придёт уведомление!",
                    show_alert=True)


async def error(func_name, err):
    err_text = f"Error in {func_name}: {err}"
    print(err_text)


async def reg_modules_process(tID):
    avaliable_modules = await get_registered_modules(tID)
    if len(avaliable_modules) < config_data['modules_count']:
        modules[tID] = []
        modules_list = await get_modules_list()
        mk = types.InlineKeyboardMarkup(row_width=1)
        for a in range(len(modules_list)):
            mk.add(types.InlineKeyboardButton(text=modules_list[a]['module_name'],
                                              callback_data=f"children_addmodule_{modules_list[a]['tutor_id']}"))
        await bot.send_message(text=f"Выбери модуль №{len(avaliable_modules) + 1}", reply_markup=mk, chat_id=tID)
    else:
        text_to_send = "*Список модулей, на который ты записан(-а)*"
        for a in range(len(avaliable_modules)):
            module_info = await get_module_info(avaliable_modules[a]['module_id'])
            text_to_send += f"\n\n*{a + 1}. {module_info['module_name']}*\nЛокация: *{module_info['location']}*"
        text_to_send += "\n\nЕсли ты хочешь изменить один из образовательных модулей, то напиши сюда: @lrrrtm"
        await bot.send_message(chat_id=tID, text=text_to_send)


async def seats(module_id):
    cur.execute(f"SELECT seats_num, seats_real FROM modules WHERE tutor_id = '{module_id}'")
    data = cur.fetchone()
    if data['seats_real'] < data['seats_num']:
        return True
    return False


async def send_feedback(tutor_id, tID):
    module_info = await get_module_info(tutor_id)
    cur_date_dmy = datetime.datetime.now().strftime("%d.%m.%Y")
    doc = DocxTemplate(fr"{project_folder}\assets\feedback_template.docx")
    context = {"module_name": module_info['module_name'],
               "feedback_date": cur_date_dmy,
               "create_time": datetime.datetime.now().strftime("%d.%m.%Y в %H:%M"),
               }
    fb = await get_feedback_by_module(tutor_id)
    if len(fb) != 0:
        for a in range(len(fb)):
            if a < len(fb):
                context[f"answer{a + 1}"] = fb[a]['answer']
            else:
                context[f"{a + 1}"] = " "
        doc.render(context)
        src = fr"{project_folder}\files\docs\fb_docs\{module_info['module_name']}-{cur_date_dmy}.docx"
        src_pdf = fr"{project_folder}\files\pdf\{module_info['module_name']}-{cur_date_dmy}.pdf"
        with open(src, "w") as f:
            f.close()
        doc.save(src)
        msg = await bot.send_message(chat_id=tID, text="Отчёт по обратной связи создаётся...")
        pdf_convert(src, src_pdf)
        await bot.delete_message(chat_id=tID, message_id=msg.message_id)
        await bot.send_document(chat_id=tID, document=open(src_pdf, 'rb'))
    else:
        await bot.send_message(chat_id=tID, text=f"По модулю {module_info['module_name']} отсутствует "
                                                 f"обратная связь за {cur_date_dmy}")


async def update_config():
    try:
        with open(f'{project_folder}\config.json', encoding='utf-8', mode="w") as f:
            json.dump(config_data, f)
        return True
    except Exception as e:
        error(update_config.__name__, e)
        return False


async def check_status(tid, st):
    try:
        cur.execute(f"SELECT status FROM admins WHERE tid = {tid}")
        status = cur.fetchall()
        print(status)
        if len(status) != 0:
            if status[0]['status'] == st:
                return True
        return False
    except Exception as e:
        error(check_status.__name__, e)


@dp.message_handler(state=Radio.request)
async def cmd_radio_request(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == "/start":
        await cmd_start(message)
    else:
        text_to_admin = "*Новая заявка!*" \
                        f"\n\n{message.text.strip()}"
        mk = types.InlineKeyboardMarkup(row_width=2)
        mk.row(types.InlineKeyboardButton(text="Принять 🟢", callback_data=f"admin_approveradio_{message.chat.id}"),
               types.InlineKeyboardButton(text="Отклонить 🔴", callback_data=f"admin_declineradio_{message.chat.id}")
               )
        radio_flags.append(message.chat.id)
        print(radio_flags)
        await bot.send_message(chat_id=config_data['chat_ids']['radio'], text=text_to_admin, reply_markup=mk)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        await bot.send_message(chat_id=message.chat.id, text="*Новая заявка на радио*"
                                                             "\n*Твоя заявка отправлена и ждёт подтверждения*"
                                                             f"\n\nТекст твоей заявки: {message.text.strip()}")


@dp.message_handler(commands=['setupmain', 'setupradio', 'setupfback', 'setupmodules'])
async def cmd_setup(message: types.Message):
    tID = message.from_user.id
    if await check_status(tID, "admin"):
        command = message.get_command()[1:].split('setup')[1]
        config_data['chat_ids'][command] = message.chat.id
        if await update_config():
            await message.answer(text=f"Данная беседа установлена как основная для {command}")
        else:
            await message.answer(text=f"Произошла ошибка при изменении конфигурации")
    else:
        await message.answer(text="*Ваш уровень доступа не позволяет выполнить данную команду.*"
                                  "\n\nЕсли вы считаете, что произошла ошибка, свяжитесь с администратором")


@dp.message_handler(commands=['radio'])
async def cmd_radio_control(message: types.Message):
    tID = message.chat.id
    if tID == config_data['chat_ids']['radio']:
        if message.chat.id == config_data['chat_ids']['radio']:
            mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            mk.add(types.KeyboardButton(text="🟢 ВКЛЮЧИТЬ РАДИО 🟢"))
            mk.add(types.KeyboardButton(text="🔴 ВЫКЛЮЧИТЬ РАДИО 🔴"))
            await message.answer(text="Клавиатура управления радио активирована", reply_markup=mk)
        else:
            await message.answer(text=f"*Управление радио доступно только из беседы [РАДИО]*")
    else:
        await message.answer(text="*Ваш уровень доступа не позволяет выполнить данную команду.*"
                                  "\n\nЕсли вы считаете, что произошла ошибка, свяжитесь с администратором")


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    start_param = message.get_args()
    tID = message.chat.id
    print(start_param, tID)
    if str(tID)[0] != "-":
        if start_param:
            start_data = start_param.split("_")
            if start_data[0] == "resolume" and await check_status(tID, 'admin'):
                await message.answer(
                    text="Чтобы добавить новый элемент в Resolume, отправьте его в формате документа. Поддерживаются изображения и видео")
            else:
                info_by_phrase = await get_info_by_phrase(start_data[0], start_data[1], tID)
                if info_by_phrase:
                    if start_data[0] == "admins":
                        if info_by_phrase['status'] == "tutor":
                            await add_tutor_to_module(tID, info_by_phrase[3])
                        await message.answer(text=f"Вы успешно зарегистрированы!"
                                                  f"\n\nВаши данные: *{info_by_phrase['firstname']} {info_by_phrase['lastname']}*"
                                                  f"\nДолжность/модуль: *{info_by_phrase['post']}*"
                                                  f"\nГруппа: *{config_data['statuses'][info_by_phrase['status']]['rus']}*"
                                                  f"\n\n*Чтобы использовать бота, нажмите или отправьте /start*")

                    elif start_data[0] == "children":
                        await message.answer(text=f"*{config_data['welcome_text']}*"
                                                  f"\n\nТвои данные: *{info_by_phrase['firstname']} {info_by_phrase['lastname']}*"
                                                  f"\nГруппа: {info_by_phrase['group_num']}"
                                                  f"\n\n*Чтобы использовать бота, нажмите или отправьте /start*")
                elif info_by_phrase is False:
                    await message.answer(
                        text="По этому QR-коду уже зарегистрировался кто-то другой. Если это не так, обратитесь к администратору")

        else:
            reg_info = await registered(tID)
            if reg_info is False:
                await message.answer(
                    "Привет!\nЯ бот Центра Развития Одарённых Детей. Если у тебя есть QR-код, отсканируй его, тогда ты сможешь зарегистрироваться!")
                pass
            else:
                text = "*Главное меню*"
                if reg_info == "admin":
                    mk = admin_markup
                elif reg_info == "mentors":
                    mk = mentor_markup
                elif reg_info == "tutor":
                    mk = tutor_markup
                elif reg_info == "children":
                    text = "*С возвращением! Что ты хочешь сделать? Выбери и нажми на нужную кнопку*" \
                           "\n\nВажно: если вдруг что-то не работает, обратись с вопросом к воспитателям, они помогут тебе решить любую проблему"
                    mk = children_markup
                await message.answer(text=text,
                                     reply_markup=mk)
    else:
        await message.answer(text="*Данную команду нельзя использовать в этом чате*")


@dp.message_handler(content_types=['text'])
async def testf(message: types.Message):
    if message.chat.id == config_data['chat_ids']['radio'] and message.text in ['🟢 ВКЛЮЧИТЬ РАДИО 🟢',
                                                                                '🔴 ВЫКЛЮЧИТЬ РАДИО 🔴']:
        global radio_status
        if message.text == "🔴 ВЫКЛЮЧИТЬ РАДИО 🔴":
            radio_status = False
            await bot.send_message(message.chat.id, "*Радио выключено, заявки не принимаются!*")
        else:
            radio_status = True
            await bot.send_message(message.chat.id, "*Радио включено, идёт отправка сообщений детям*")
            cur.execute(f"SELECT tid, firstname FROM children")
            data = cur.fetchall()
            if data:
                for child in data:
                    await bot.send_message(chat_id=child['tid'],
                                           text=f"*{child['firstname']}, наше радио в эфире! Скорее отправляй свои приветы и песни, чтобы их услышал весь ЦРОД!*",
                                           reply_markup=types.InlineKeyboardMarkup().add(
                                               types.InlineKeyboardButton(text="Отправить заявку на радио 📻",
                                                                          callback_data="children_radio")))


async def on_startup(dp):
    try:
        await bot.send_message(chat_id=config_data['chat_ids']['radio'], text='*Система CROD.CONNECT перезапущена*'
                                                                              '\nТекущий статус радио: выключено.'
                                                                              '\n\n_Для показа клавиатуры управления нажмите /radio_')
        await bot.send_message(chat_id=config_data['chat_ids']['fback'], text='*Система CROD.CONNECT перезапущена*'
                                                                              '\nМодуль обратной связи активен')
        await bot.send_message(chat_id=config_data['chat_ids']['modules'], text='*Система CROD.CONNECT перезапущена*'
                                                                                '\nМодуль обработки запросов по образовательным модулям активен')
    except Exception:
        pass


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
