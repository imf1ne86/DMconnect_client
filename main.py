"""
* Клиент DMconnect
* *************************
* Программа представляет собой клиент DMconnect.
* DMconnect Web: http://dmconnect.hoho.ws:777
* Для работы программы требуется Python 3. Предварительно
* требуется установить необходимые библиотеки:
* $ pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip
* Программа является кроссплатформенной. Она должна работать
* под Microsoft Windows, Linux, macOS и т.д.
*
* @author Ефремов А. В., 15.10.2025
"""

import sys, os
from typing import List, Set
from tkinter import *
from tkinter import ttk

from dmconnect import DMconnect
from miscellaneous import Miscellaneous

# --- Константы ---
ICON_FILE: str = os.path.join(os.path.join(os.path.dirname(__file__), "."), "logo.ico")
FONT_FACE: str = "Courier New"
FONT_BGCOLOR: str = "#F5F5DC" # https://python-charts.com/colors/
REFRESH_INTERVAL_MS: int = 5 * 1000 # интервал обновления чата в миллисекундах (чем больше время, тем ниже отзывчивость программы для пользователя)

# --- Основное окно ---
root: Tk = None
try:
    root = Tk()
except Exception:
    Miscellaneous.print_message("Для работы программы требуется графический интерфейс.")
    sys.exit()

class Application:

    objDMconnect: DMconnect = None

    def __init__(self):
        self.objDMconnect = DMconnect(root)

        self.apply_icon()
        self.build_app()

        # Получаем и отображаем список пользователей после создания UI
        self.user_listbox_items = self.get_user_list()
        self.populate_users_listbox()

        # Запускаем периодическое обновление чата
        self.schedule_message_update()

    # --- Основные функции программы (расположены после __init__ для удобства) ---

    def get_user_list(self) -> List[str]:
        """
        * Возвращает массив логинов пользователей
        *
        * @return Список пользователей
        """
        user_list = []
        if self.objDMconnect.is_connected:
            user_list = self.objDMconnect.get_user_list()
            if len(self.objDMconnect.left_for_chat) > 0: # есть что-нибудь для чата?
                for line in self.objDMconnect.left_for_chat:
                    self.add_message_to_chat(line)
        return user_list

    def get_messages_for_chat(self) -> List[str]:
        """
        * Возвращает массив новых строк для чата
        *
        * @return Список строк для чата
        """
        messages = []
        if self.objDMconnect.is_connected:
            self.user_listbox_items = self.get_user_list()
            self.populate_users_listbox()
            messages = self.objDMconnect.get_messages_for_chat()
        return messages

    # --- Основные методы класса ---

    def apply_icon(self) -> None:
        """
        * Применение иконки для программы (файл "*.ico")
        """
        if Miscellaneous.is_file_readable(ICON_FILE):
            sys_prop = Miscellaneous.get_system_properties()
            try:
                if sys_prop[0] == "Windows":
                    root.wm_iconbitmap(default = ICON_FILE)
                else:
                    root.iconbitmap(ICON_FILE)
            except Exception as e:
                Miscellaneous.print_message(f"Ошибка при загрузке иконки '{ICON_FILE}': {e}")

    def on_close(self):
        self.quit_app()

    def build_app(self) -> None:
        """
        * Построение конечного UI для текущего приложения
        """
        global root
        root.title("Клиент DMconnect")
        root.geometry("900x600")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- Стили для ttk виджетов ---
        style = ttk.Style()
        style.configure("TEntry", fieldbackground=FONT_BGCOLOR, font=(FONT_FACE, 10))
        style.configure("Accent.TButton", padding=5)

        # --- Основная структура окна ---
        chat_and_users_container = ttk.Frame(root)
        chat_and_users_container.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(5, 0))

        input_container = ttk.Frame(root, height=80)
        input_container.pack(side=BOTTOM, fill=X, padx=5, pady=(0, 5))

        # --- Разделение верхней области на чат и список пользователей ---
        # Левая часть: область чата с возможностью прокрутки
        chat_frame = ttk.Frame(chat_and_users_container)
        chat_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))

        self.chat_text = Text(chat_frame, wrap=WORD, state=DISABLED, font=(FONT_FACE, 10), bg=FONT_BGCOLOR)
        self.chat_text.pack(side=LEFT, fill=BOTH, expand=True)

        self.chat_scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_text.yview)
        self.chat_scrollbar.pack(side=RIGHT, fill=Y)
        self.chat_text.config(yscrollcommand=self.chat_scrollbar.set)

        # Правая часть: список пользователей с возможностью прокрутки
        users_frame = ttk.Frame(chat_and_users_container, width=180)
        users_frame.pack(side=RIGHT, fill=Y)

        self.users_listbox = Listbox(users_frame, selectmode=SINGLE, font=(FONT_FACE, 10), bg=FONT_BGCOLOR)
        self.users_listbox.pack(side=LEFT, fill=BOTH, expand=True)

        self.users_scrollbar = ttk.Scrollbar(users_frame, command=self.users_listbox.yview)
        self.users_scrollbar.pack(side=RIGHT, fill=Y)
        self.users_listbox.config(yscrollcommand=self.users_scrollbar.set)

        self.users_listbox.bind("<Double-Button-1>", self.on_user_double_click)

        # --- Настройка нижней области (input_container) ---
        self.message_entry = ttk.Entry(input_container, style="TEntry", font=(FONT_FACE, 10))
        self.message_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", self.send_message_event)

        self.send_button = ttk.Button(input_container, text="Отправить", command=self.send_message, style="Accent.TButton")
        self.send_button.pack(side=RIGHT)

    def populate_users_listbox(self) -> None:
        """
        * Заполняет Listbox пользователями из self.user_listbox_items
        """
        self.users_listbox.delete(0, END)
        for user in self.user_listbox_items:
            self.users_listbox.insert(END, user)

    def send_message_event(self, event):
        """
        * Обработчик нажатия Enter в поле ввода
        """
        self.send_message()
        return "break"

    def send_message(self):
        """
        * Отправка сообщения
        """
        if self.objDMconnect.is_connected:
            message = self.message_entry.get()
            if message:
                self.add_message_to_chat(f"Вы: {message}")
                self.message_entry.delete(0, END)
                response_lines: Set[str] = set()
                response_lines = self.objDMconnect.execute_command(self.objDMconnect.sock, message)
                Miscellaneous.print_message(f"Отправлено: {message}")
                Miscellaneous.print_message("Ниже приведены строки ответа от сервера.")
                for response_line in response_lines:
                    self.add_message_to_chat(response_line)
                    print(response_line)
                Miscellaneous.print_message("Конец печати строк ответа от сервера.")

                self.user_listbox_items = self.get_user_list()
                self.populate_users_listbox()

    def add_message_to_chat(self, message: str):
        """
        * Добавляет сообщение в область чата
        """
        self.chat_text.config(state=NORMAL)
        self.chat_text.insert(END, message + "\n")
        self.chat_text.config(state=DISABLED)
        self.chat_text.see(END)

    def update_chat_messages(self):
        """
        * Получает новые сообщения и добавляет их в чат
        """
        new_messages = self.get_messages_for_chat()
        if new_messages:
            for msg in new_messages:
                self.add_message_to_chat(msg)
        self.schedule_message_update()

    def schedule_message_update(self):
        """
        * Планирует следующее обновление сообщений чата
        """
        if not self.objDMconnect.is_connected:
            Miscellaneous.print_message("Нет соединения с сервером.")
        root.after(REFRESH_INTERVAL_MS, self.update_chat_messages)

    def on_user_double_click(self, event):
        """
        * Обработчик двойного клика по пользователю в списке
        """
        widget = event.widget
        index = widget.curselection()
        if index:
            selected_user = widget.get(index[0])

            current_text = self.message_entry.get()
            cursor_position = self.message_entry.index(INSERT)

            new_text = current_text[:cursor_position] + selected_user + current_text[cursor_position:]

            self.message_entry.delete(0, END)
            self.message_entry.insert(0, new_text)
            self.message_entry.icursor(cursor_position + len(selected_user))

    def quit_app(self) -> None:
        """
        * Завершение работы программы
        """
        global root
        if self.objDMconnect is not None: # попытка корректного завершения работы с сервером DMconnect
            if self.objDMconnect.is_connected == True and self.objDMconnect.sock is not None:
                try:
                    self.objDMconnect.sock.close()
                except Exception:
                    pass
                self.objDMconnect.sock = None
                self.objDMconnect.is_connected = False
        root.destroy()
        root.quit()
        Miscellaneous.print_message("Работа программы завершена.")
        sys.exit()

def main() -> None:
    objApp: Application = Application()
    root.mainloop()

if __name__ == "__main__":
    main()
