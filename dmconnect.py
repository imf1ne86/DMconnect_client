"""
* Класс для подключения к серверу DMconnect
* *************************
* Документацию по протоколу DMconnect можно изучить на
* сайте: https://dmconnectspec.w10.site
* Исходный код сервера DMconnect является открытым, и этот
* код можно изучить на GitHub: http://github.com/tankwars92/DMCD/
*
* @author Ефремов А. В., 15.10.2025
"""

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from typing import List, Set
from socket import socket, AF_INET, SOCK_STREAM, timeout
from socket import SOL_SOCKET, SO_KEEPALIVE, IPPROTO_TCP
try: # решение проблемы "ImportError: cannot import name 'TCP_KEEPCNT' from 'socket'"
    from socket import TCP_KEEPCNT
except ImportError:
    TCP_KEEPCNT = None
try: # решение проблемы "ImportError: cannot import name 'TCP_KEEPINTVL' from 'socket'"
    from socket import TCP_KEEPINTVL
except ImportError:
    TCP_KEEPINTVL = None
try: # решение проблемы "ImportError: cannot import name 'TCP_KEEPIDLE' from 'socket'"
    from socket import TCP_KEEPIDLE
except ImportError:
    TCP_KEEPIDLE = None
import sys
import time
import random
import configparser

from miscellaneous import Miscellaneous
from models import Constant

CODEPAGE: str = "utf-8" # используемая кодировка
NEW_LINE: str = "\n" # признак новой строки
DELAY: float = 0.3 # интервалы между отправками данных серверу (в секундах)
LIST_OF_USERS: str = "Members in " # признак списка пользователей в ответе от сервера

debugged: bool = False # режим отладки (по умолчанию отключён)

class DMconnect:

    connect_window: Toplevel = None
    root: Tk = None # родительское окно

    sock: socket = None
    is_connected: bool = False
    left_for_chat: Set[str] = set() # строки ответа от сервера для чата

    def __init__(self, p_parent: Tk):
        self.root = p_parent
        self.get_config()
        if debugged:
            self.is_connected = True
        self.build_connect_form()

    def get_user_list(self) -> List[str]:
        """
        * Возвращает массив логинов пользователей
        *
        * @return Список пользователей
        """
        if debugged: # в режиме отладки возвращаем фиксированный список пользователей без обращения в сеть
            return [name.strip() for name in "Bepyaka, logger, arson-test, pro_O, Khrich, kopor'je, Archie, guester, 0010, root, dm906, Peacemaker, ZiNc".split(',')]
        user_list = []
        if self.is_connected: # есть вообще подключение к серверу?
            usr: str = ""
            response_lines: List[str] = []
            if not debugged:
                Miscellaneous.print_message("Запрос у сервера списка участников чата...")
                response_lines = self.execute_command(self.sock, "/members")
                Miscellaneous.print_message("Ниже приведены строки ответа от сервера.")
                for response_line in response_lines:
                    print(response_line)
                Miscellaneous.print_message("Конец печати строк ответа от сервера.")
            else:
                response_lines.add(f"{LIST_OF_USERS}'general': Bepyaka, logger, arson-test, pro_O, Khrich, kopor'je, Archie, guester, 0010, root, dm906, Peacemaker, ZiNc, bwMate, IRC_bridge, Vasylich, perliT@geeks.l5.ca, dymka2@linuxers.hs.vc, usr34098")
                response_lines.add("user01: test2")
                response_lines.add(f"{LIST_OF_USERS}'dsalin_': John, Peter,Joe, Вася,   Bethany, Пётр,Mark,John, Peter,Joe, Вася,John, Peter,Joe, Вася,John, Peter,Joe, Вася,John, Peter,Joe, Вася,John, Peter,Joe, Вася,John, Peter,Joe, Вася,John, Peter,Joe, Вася")
            self.left_for_chat.clear()
            for line in response_lines: # проверяем, есть ли что-нибудь от сервера для чата в ответе
                if not line.startswith(LIST_OF_USERS):
                    self.left_for_chat.add(line)
            members_line: str = None
            for line in response_lines:
                if line.startswith(LIST_OF_USERS):
                    members_line = line
                    break
            if members_line is not None:
                parts = members_line.split(':', 1)
                if len(parts) == 2:
                    usr = parts[1].lstrip()  # берём всё после первого ':' без изменений (убираем только ведущие пробелы)
            if not "".__eq__(usr):
                user_list = [name.strip() for name in usr.split(',')]
        return user_list

    def get_messages_for_chat(self) -> List[str]:
        """
        * Возвращает массив новых строк для чата
        *
        * @return Список строк для чата
        """
        messages = []
        if self.is_connected: # есть вообще подключение к серверу?
            if not debugged:
                Miscellaneous.print_message("Запрос у сервера сообщений чата...")
                response_lines: List[str] = []
                response_lines = self.read_socket(self.sock)
                Miscellaneous.print_message("Ниже приведены строки ответа от сервера.")
                for response_line in response_lines:
                    messages.append(response_line)
                Miscellaneous.print_message("Конец печати строк ответа от сервера.")
            else:
                if random.choice([True, False, False]): # Пример: ~33% шанс получить новые сообщения
                    messages.append("Alex: Привет всем!")
                if random.choice([True, False, False]):
                    messages.append("Guest: Как дела?")
                if random.choice([True, False, False]):
                    messages.append("Admin: Не забывайте про правила.")
        return messages

    def get_config(self) -> None:
        """
         * Получение конфигурации программы
        """
        global debugged
        GLOBAL_SECTION: str = "global"
        DEBUG: str = "debug"
        if Miscellaneous.is_file_readable(Constant.SETTINGS_FILE.value):
            config = configparser.ConfigParser()
            try:
                with open(Constant.SETTINGS_FILE.value, 'r', encoding=Constant.GLOBAL_CODEPAGE.value) as f:
                    config.read_file(f)
                    if not debugged: # включали и настраивали уже отладку?
                        if GLOBAL_SECTION in config and DEBUG in config[GLOBAL_SECTION]:
                            debugged = (config[GLOBAL_SECTION][DEBUG].upper().strip() == "Y")
                            if debugged:
                                Miscellaneous.print_message("Включён режим отладки.")
            except FileNotFoundError:
                Miscellaneous.print_message(f"Ошибка: Файл настроек не найден: {Constant.SETTINGS_FILE.value}")
                raise
            except Exception as e:
                Miscellaneous.print_message(f"Ошибка при чтении файла настроек: {e}")
                raise

    def build_connect_form(self):
        """
        * Форма аутентификации и подключения к серверу
        """
        self.connect_window = Toplevel(self.root)
        self.connect_window.grab_set() # захват ввода (модальность)
        # self.connect_window.lift() # поднять над другими окнами
        # self.connect_window.focus_force() # силой дать фокус окну (может не сработать в всех ОС)
        self.connect_window.title("Форма подключения")
        self.connect_window.geometry("400x350")
        self.connect_window.resizable(False, False)
        self.connect_window.deiconify()
        self.root.after(3 * 1000, lambda: (self.connect_window.lift(), self.connect_window.focus_force()))

        form_frame = ttk.Frame(self.connect_window, padding="10")
        form_frame.pack(fill=BOTH, expand=True)

        ttk.Label(form_frame, text="Хост сервера:").grid(row=0, column=0, sticky=W, pady=(0, 2), padx=5)
        self.host_entry = ttk.Entry(form_frame, width=30)
        self.host_entry.grid(row=0, column=1, pady=(0, 2), padx=5)

        ttk.Label(form_frame, text="TCP-порт сервера:").grid(row=1, column=0, sticky=W, pady=(0, 2), padx=5)
        self.port_entry = ttk.Entry(form_frame, width=10)
        self.port_entry.grid(row=1, column=1, sticky=W, pady=(0, 2), padx=5)

        ttk.Label(form_frame, text="Логин:").grid(row=2, column=0, sticky=W, pady=(0, 2), padx=5)
        self.login_entry = ttk.Entry(form_frame, width=30)
        self.login_entry.grid(row=2, column=1, pady=(0, 2), padx=5)

        ttk.Label(form_frame, text="Пароль:").grid(row=3, column=0, sticky=W, pady=(0, 2), padx=5)
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.grid(row=3, column=1, pady=(10, 10), padx=5)

        connect_button = ttk.Button(form_frame, text="Подключиться", command=self.on_connect_button_click)
        connect_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.status_bar_label = ttk.Label(self.connect_window, text=" ", relief=SUNKEN, anchor=W, background="#D3D3D3", foreground="black", padding=(5, 2))
        self.status_bar_label.pack(side=BOTTOM, fill=X)

        self.update_status_bar()
        self.host_entry.focus_set()

    def on_connect_button_click(self):
        host = self.host_entry.get()
        port_str = self.port_entry.get()
        login = self.login_entry.get()
        password = self.password_entry.get()

        port = None
        if port_str:
            try:
                port = int(port_str)
                if not (1 <= port <= 65534):
                    port = None
            except ValueError:
                port = None

        if not host or port is None or not login or not password:
            messagebox.showwarning("Ошибка ввода", "Пожалуйста, заполните все поля корректно.")
            return

        self.connect(host, port, login, password)

    def read_socket(self, s: socket, recv_timeout: float = 2.0) -> Set[str]:
        """
        * Чтение сокета через file-like объект
        *
        * @param s Экземпляр сокета
        * @param recv_timeout Таймаут получения ответ в мс
        * @return Массив строк
        """
        response_lines: List[str] = []
        if self.is_connected: # есть вообще подключение к серверу?
            if not debugged:
                try:
                    # читаем ответ построчно через file-like объект
                    s.settimeout(recv_timeout)
                    rf = s.makefile("r", encoding = CODEPAGE, newline = NEW_LINE)
                    try:
                        while True:
                            try:
                                # time.sleep(DELAY)
                                line: str = rf.readline()
                            except timeout:
                                break
                            if "".__eq__(line): # EOF - сервер закрыл соединение
                                self.is_connected = False
                                break
                            line = line.rstrip("\r\n")
                            if "".__eq__(line): # пустая строка - считаем конец ответа
                                break
                            response_lines.append(line)
                    finally:
                        try:
                            rf.close()
                        except Exception:
                            pass
                except Exception:
                    try:
                        s.close()
                    except Exception:
                        pass
                    self.sock = None
                    self.is_connected = False
                    raise
        return response_lines

    def execute_command(self, s: socket, cmd: str) -> Set[str]:
        """
        * Команда для сервера
        *
        * @param s Экземпляр сокета
        * @param cmd Команда
        * @return Массив строк
        """
        cmd2: str = f"{cmd}{NEW_LINE}"
        response_lines: List[str] = []
        if self.is_connected: # есть вообще подключение к серверу?
            if not debugged:
                try:
                    s.sendall(cmd2.encode(CODEPAGE))
                    time.sleep(DELAY)
                    response_lines = self.read_socket(s)
                except Exception:
                    try:
                        s.close()
                    except Exception:
                        pass
                    self.sock = None
                    self.is_connected = False
                    raise
        return response_lines
    
    def establish_connection(self, host: str, port: int, login: str, password: str) -> None:
        """
        * Установка сетевого соединения с сервером
        *
        * @param host Доменное имя хоста сервера DMconnect или его IP-адрес
        * @param port TCP-порт сервера DMconnect
        * @param login Имя пользователя на сервере DMconnect
        * @param password Пароль пользователя на сервере DMconnect
        """
        Miscellaneous.print_message(f"Попытка подключения к {host}:{port} с логином {login}...")
        s: socket = socket(AF_INET, SOCK_STREAM)
        """
        * *************************
        * УСТАНОВКА СОЕДИНЕНИЯ KEEP-ALIVE
        * (НАЧАЛО)
        * *************************
        """
        TCP_KEEPALIVE: int = 0x10
        try:
            s.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
            if sys.platform.startswith("linux"):
                if hasattr(socket, "TCP_KEEPIDLE"):
                    s.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, 60) # время простоя до первого keepalive
                if hasattr(socket, "TCP_KEEPINTVL"):
                    s.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, 10) # интервал между keepalive
                if hasattr(socket, "TCP_KEEPCNT"):
                    s.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 3) # число попыток до разрыва
            elif sys.platform.startswith("darwin") or "bsd" in sys.platform:
                s.setsockopt(IPPROTO_TCP, TCP_KEEPALIVE, 60)
        except AttributeError:
            pass # какая-то опция не поддерживается на текущей платформе
        except OSError:
            pass # ошибка при установке опции
        """
        * *************************
        * УСТАНОВКА СОЕДИНЕНИЯ KEEP-ALIVE
        * (КОНЕЦ)
        * *************************
        """
        try:
            s.setblocking(False)
            s.settimeout(5.0)
            s.connect((host, port))
            self.sock = s # сохраняем сокет в экземпляре для дальнейшего использования
            self.is_connected = True
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            self.sock = None
            self.is_connected = False
            raise
        cmd: str = f"/login {login} {password}"
        response_lines: Set[str] = set()
        response_lines = self.execute_command(s, cmd)
        Miscellaneous.print_message("Ниже приведены строки ответа от сервера.")
        for response_line in response_lines:
            print(response_line)
        Miscellaneous.print_message("Конец печати строк ответа от сервера.")
        if self.sock is not None:
            self.is_connected = True # успешное подключение
        else:
            self.is_connected = False
        Miscellaneous.print_message(f"Подключение {'установлено' if self.is_connected else 'не установлено'}.")

    def connect(self, host: str, port: int, login: str, password: str) -> None:
        if not debugged:
            self.establish_connection(host, port, login, password)
        else:
            self.is_connected = True # успешное подключение

        self.update_status_bar()

        if self.is_connected:
            if self.connect_window:
                self.connect_window.destroy() # закрываем окно подключения
                self.connect_window = None

    def update_status_bar(self) -> None:
        if self.status_bar_label:
            if self.is_connected:
                self.status_bar_label.config(text="Подключение к серверу установлено.")
            else:
                self.status_bar_label.config(text="Отсутствует подключение к серверу.")
