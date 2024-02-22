import datetime

from bot import connection, cur, error


async def get_info_by_phrase(table: str, phrase: str, tID: str):
    try:
        cur.execute(f"SELECT * FROM {table} WHERE pass_phrase = '{phrase}'")
        print(f"SELECT * FROM {table} WHERE pass_phrase = '{phrase}'")
        data = cur.fetchall()
        if len(data) == 0:
            return False
        else:
            if data[0]['tid'] is None:
                print(f"UPDATE {table} SET tID = {tID} WHERE pass_phrase = '{phrase}'")
                cur.execute(f"UPDATE {table} SET tID = {tID} WHERE pass_phrase = '{phrase}'")
                connection.commit()
                return data[0]
            else:
                return False
    except Exception as e:
        error(get_info_by_phrase.__name__, e)


async def registered(tID: int):
    try:
        cur.execute(f"SELECT * FROM admins WHERE tid = {tID}")
        data_admins = cur.fetchall()
        cur.execute(f"SELECT * FROM children WHERE tid = {tID}")
        data_children = cur.fetchall()
        if len(data_admins) != 0:
            return data_admins[0]['status']  # возвращает статус
        elif len(data_children) != 0:
            return "children"
        else:
            return False
    except Exception as e:
        error(registered.__name__, e)


async def add_tutor_to_module(tID, module):
    try:
        print(f"UPDATE modules SET tutor_id = {tID} WHERE name = '{module}'")
        cur.execute(f"UPDATE modules SET tutor_id = {tID} WHERE name = '{module}'")
        connection.commit()
    except Exception as e:
        error(add_tutor_to_module.__name__, e)


async def get_module_name(tutor_id):
    try:
        cur.execute(f"SELECT name FROM modules WHERE tutor_id = {tutor_id}")
        data = cur.fetchall()[0][0]
        return data
    except Exception as e:
        error(get_info_by_phrase.__name__, e)


async def get_mentor_group(tutor_id):
    try:
        cur.execute(f"SELECT post FROM admins WHERE tid = {tutor_id}")
        data = cur.fetchall()[0][0]
        return data
    except Exception as e:
        error(get_info_by_phrase.__name__, e)


async def get_children_list(filter, value):
    try:
        if filter == "modules":  # выборка, если идёт поиск по одному из модулей
            cur.execute(f"SELECT * FROM children WHERE \"{value}\" = ANY(modules)")
        else:
            cur.execute(f"SELECT lastname, firstname FROM children WHERE \"{filter}\" = '{value}'")
            print(f"SELECT lastname, firstname FROM children WHERE \"{filter}\" = '{value}'")
        data = cur.fetchall()
        print(data)
        return data
    except Exception as e:
        error(get_children_list.__name__, e)


async def add_module_to_children(child_id, module_id):
    try:
        cur.execute(f"INSERT INTO modules_in (child_id, module_id) VALUES ({child_id}, {module_id})")
        connection.commit()
        cur.execute(f"UPDATE modules SET seats_real = seats_real + 1 WHERE tutor_id = '{module_id}'")
        connection.commit()
    except Exception as e:
        error(add_module_to_children.__name__, e)


async def get_count_of_registered_modules(child_id):
    try:
        cur.execute(f"SELECT COUNT(*) FROM modules_in WHERE child_id = {child_id}")
        data = cur.fetchone()
        return data
    except Exception as e:
        error(get_count_of_registered_modules.__name__, e)


async def get_registered_modules(child_id):
    try:
        cur.execute(f"SELECT module_id from modules_in WHERE child_id = {child_id}")
        data = cur.fetchall()
        return data
    except Exception as e:
        error(get_registered_modules.__name__, e)


async def check_feedback(tID, module, date):
    try:
        cur.execute(
            f"SELECT COUNT(*) AS rows_count FROM feedback WHERE tid = {tID} AND module = '{module}' and date = '{date}'")
        count = cur.fetchall()
        return count
    except Exception as e:
        error(check_feedback.__name__, e)


async def add_feedback(module, text, grade):
    try:
        cur.execute(
            f"INSERT INTO feedback (module_name, answer, grade, date) VALUES ('{module}', '{text}', {grade}, CURRENT_DATE)")
        connection.commit()
    except Exception as e:
        error(add_feedback.__name__, e)


async def get_feedback_by_module(module_id):
    try:
        cur.execute(
            f"SELECT * FROM feedback WHERE module_id = '{module_id}' and answer_date = '{datetime.datetime.now().strftime('%Y-%m-%d')}'")
        data = cur.fetchall()
        return data
    except Exception as e:
        error(get_feedback_by_module.__name__, e)
        return False


async def get_modules_list():
    try:
        cur.execute(f"SELECT * FROM modules")
        data = cur.fetchall()
        return data
    except Exception as e:
        error(get_modules_list.__name__, e)


async def get_user_from_admin(column, value):
    try:
        cur.execute(f"SELECT * FROM admins WHERE \"{column}\" = '{value}'")
        data = cur.fetchall()
        return data[0]
    except Exception as e:
        error(get_user_from_admin.__name__, e)


async def get_module_info(tutor_id):
    try:
        cur.execute(f"SELECT * FROM modules WHERE tutor_id = '{tutor_id}'")
        data = cur.fetchall()
        return data[0]
    except Exception as e:
        error(get_module_info.__name__, e)
