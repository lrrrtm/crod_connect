from aiogram.types import InlineKeyboardMarkup as imarkup, InlineKeyboardButton as ibutton

admin_markup = imarkup(row_width=2)
mentor_markup = imarkup(row_width=1)
tutor_markup = imarkup(row_width=1)
children_markup = imarkup(row_width=1)

grades_markup = imarkup(row_width=5)

tutor_markup.add(
    ibutton(text="Список модуля", callback_data="tutor_childrenlist"),
    ibutton(text="Обратная связь", callback_data="tutor_getfeedback"),
)

admin_markup.add(
    ibutton(text="Обратная связь", callback_data="admin_getfeedback"),
    ibutton(text="Статистика", callback_data="admin_stat"),
    ibutton(text="Измение группы", callback_data="admin_changegroup"),
    ibutton(text="Изменение модуля", callback_data="admin_changemodule"),
    ibutton(text="Удаление", callback_data="admin_changemodule"),
    ibutton(text="Перезапуск смены", callback_data="admin_restart"),

)

mentor_markup.add(
    ibutton(text="Список группы", callback_data="mentors_childrenlist"),
    ibutton(text="Статистика по обратке", callback_data="mentors_stat"),
    ibutton(text="QR-коды", callback_data="mentors_qr"),

)

children_markup.add(
    ibutton(text="Обратная связь 🗣️", callback_data="children_sendfeedback"),
    ibutton(text="Образовательные модули 💡", callback_data="children_modules"),
    ibutton(text="Радио 📻", callback_data="children_radio"),
)

for a in range(5):
    grades_markup.add(ibutton(text=f"{a+1}", callback_data=f"children_setgrade_{a+1}"))