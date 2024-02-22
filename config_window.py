import datetime
import json
import os
import subprocess
import time

import flet as ft
import psutil

from app import config_file_name

script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
os.chdir(script_directory)
project_folder = os.getcwd()


def main_config(page: ft.Page):
    page.title = "Конфигурация CROD Connect"
    page.window_always_on_top = True
    page.window_skip_task_bar = True
    page.window_maximizable = False
    page.window_minimizable = False
    page.window_resizable = False

    page.window_width = 500
    page.window_height = 950
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    page.theme = ft.Theme(font_family="Montserrat")
    page.fonts = {
        "Montserrat": "fonts/Montserrat-SemiBold.ttf",
    }
    page.theme_mode = ft.ThemeMode.LIGHT

    def check_field(e):
        if all([
            main_col.controls[1].controls[0].value,
            main_col.controls[1].controls[1].value,
            main_col.controls[2].controls[0].value,
            main_col.controls[2].controls[1].value,
            main_col.controls[3].value,
            main_col.controls[6].controls[0].value,
            main_col.controls[7].controls[0].value,
            main_col.controls[7].controls[1].value,
            main_col.controls[10].controls[0].value,
            main_col.controls[11].controls[0].value,
            main_col.controls[11].controls[1].value,
            main_col.controls[12].controls[0].value,
            main_col.controls[12].controls[1].value,
            main_col.controls[15].value
        ]):
            page.floating_action_button.visible = True
        else:
            page.floating_action_button.visible = False
        if e.control.value == "":
            e.control.border_color = ft.colors.RED
        else:
            e.control.border_color = ft.colors.GREEN

        page.update()

    def terminate_process_by_name(process_name: str):
        for process in psutil.process_iter(['pid', 'name']):
            if process.name() == process_name:
                try:
                    process.terminate()
                    print(f"Процесс {process_name} успешно остановлен.")
                except Exception as e:
                    print(f"Ошибка при остановке процесса {process_name}: {e}")

    def is_running(process_name: str):
        # Проверка наличия процесса в диспетчере задач

        for a in psutil.process_iter(['pid', 'name']):
            if a.name().split('.')[0] == process_name:
                return True
        return False

    def save_new_data(e):
        # Сохранение данных и запуск процесса

        config_data['database']['host'] = main_col.controls[1].controls[0].value
        config_data['database']['port'] = main_col.controls[1].controls[1].value
        config_data['database']['user'] = main_col.controls[2].controls[0].value
        config_data['database']['password'] = main_col.controls[2].controls[1].value
        config_data['database']['db_name'] = main_col.controls[3].value

        config_data['paths']['ngrok']['path'] = main_col.controls[6].controls[0].value
        config_data['paths']['ngrok']['domain'] = main_col.controls[7].controls[0].value
        config_data['paths']['ngrok']['port'] = main_col.controls[7].controls[1].value

        config_data['paths']['arena'] = main_col.controls[10].controls[0].value
        config_data['control']['address'] = main_col.controls[11].controls[0].value
        config_data['control']['port'] = main_col.controls[11].controls[1].value
        config_data['control']['resolume_start_time'] = main_col.controls[12].controls[0].value
        config_data['control']['pin'] = main_col.controls[12].controls[1].value

        config_data['bot']['token'] = main_col.controls[15].value

        old_config_path = os.path.join(project_folder, "old_config")
        config_file_path = os.path.join(project_folder, "config.json")
        cur_date = str(datetime.datetime.now()).replace(":", "-").replace(" ", "")
        new_config_path = os.path.join(old_config_path, f"old-config-{cur_date}.json")
        os.rename(config_file_path, new_config_path)

        json.dump(config_data, open('config.json', "w"), ensure_ascii=True, indent=2)

        page.dialog = ft.AlertDialog(title=ft.Text(""),
                                     actions_alignment=ft.MainAxisAlignment.END,
                                     actions=[ft.ElevatedButton(text="OK", on_click=lambda _: page.window_destroy())],
                                     content=ft.Column([ft.Text("Данные обновлены, перезагрузите Connect", size=19,
                                                                text_align=ft.TextAlign.CENTER)],
                                                       horizontal_alignment=ft.CrossAxisAlignment.CENTER, height=100,
                                                       alignment=ft.MainAxisAlignment.CENTER))
        page.dialog.open = True
        page.update()
        time.sleep(15)
        page.window_destroy()

    def open_file_picker(e: ft.ControlEvent):
        file_picker.data = e.control.data
        file_picker.pick_files()

    def set_path(e: ft.FilePickerResultEvent):

        if file_picker.data == 'ngrok':
            main_col.controls[6].controls[0].value = e.files[0].path
        elif file_picker.data == 'resolume':
            main_col.controls[10].controls[0].value = e.files[0].path
        check_field('e')
        page.update()

    with open(os.path.join(project_folder, config_file_name), encoding='utf-8', mode="r") as config_file:
        config_data = json.load(config_file)

    page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.SAVE_ROUNDED, text="Сохранить",
                                                          on_click=save_new_data, visible=False)

    db_dict = config_data['database']
    ngrok_dict = config_data['paths']['ngrok']
    arena_dict = config_data['control']

    file_picker = ft.FilePicker(on_result=set_path)
    page.overlay.append(file_picker)

    main_col = ft.Column(
        [
            ft.Row([ft.Text("База данных", size=19)]),
            ft.Row([ft.TextField(label="Хост", width=300, on_change=check_field, value=db_dict['host']),
                    ft.TextField(label="Порт", width=100, on_change=check_field, value=db_dict['port'])]),
            ft.Row([ft.TextField(label="Пользователь", width=200, on_change=check_field, value=db_dict['user']),
                    ft.TextField(label="Пароль", width=200, password=True, on_change=check_field,
                                 value=db_dict['password'])]),
            ft.TextField(label="Имя БД", width=200, on_change=check_field, value=db_dict['db_name']),
            ft.Divider(thickness=2),

            ft.Row([ft.Text("Ngrok", size=19)]),
            ft.Row([ft.TextField(label="Путь", width=300, read_only=True, on_change=check_field, data='ngrok',
                                 value=ngrok_dict['path']),
                    ft.ElevatedButton(text="Выбрать", on_click=open_file_picker, data='ngrok'), ]),
            ft.Row([ft.TextField(label="Домен", width=300, on_change=check_field, value=ngrok_dict['domain']),
                    ft.TextField(label="Порт", width=100, on_change=check_field, value=ngrok_dict['port'])]),
            ft.Divider(thickness=2),

            ft.Row([ft.Text("Resolume Arena", size=19)]),
            ft.Row([ft.TextField(label="Путь", width=300, read_only=True, data='resolume', on_change=check_field,
                                 value=config_data['paths']['arena']),
                    ft.ElevatedButton(text="Выбрать", on_click=open_file_picker, data='resolume')]),
            ft.Row([ft.TextField(label="Хост", width=300, on_change=check_field, value=arena_dict['address']),
                    ft.TextField(label="Порт", width=100, on_change=check_field, value=arena_dict['port'])]),
            ft.Row([ft.TextField(label="Время старта", width=200, on_change=check_field,
                                 value=arena_dict['resolume_start_time']),
                    ft.TextField(label="ПИН-код", width=200, password=True, on_change=check_field,
                                 value=arena_dict['pin'])]),
            ft.Divider(thickness=2),

            ft.Row([ft.Text("Telegram бот", size=19)]),
            ft.TextField(label="Токен", width=300, on_change=check_field, value=config_data['bot']['token']),

        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    page.add(main_col)
    page.update()


ft.app(target=main_config, assets_dir='assets')
