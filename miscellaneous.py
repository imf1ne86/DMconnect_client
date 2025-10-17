from datetime import datetime, timedelta
import os, sys
import socket
import psutil, platform
import random
import requests
from typing import Any
import subprocess, shlex
import feedparser
from feedparser import FeedParserDict
from urllib.request import ProxyHandler
from smtplib import SMTP, SMTP_SSL, SMTPException
from email.message import EmailMessage
import re

class Miscellaneous:

    @staticmethod
    def get_current_time() -> str:
        """
        * Получение текущей даты и времени
        *
        * @return Текущая дата и время
        """
        return datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    @staticmethod
    def print_message(msg: str) -> None:
        """
        * Вывод сообщения на экран с текущей датой и временем
        *
        * @param msg Текст сообщения
        """
        if not "".__eq__(msg):
            print(f"[{Miscellaneous.get_current_time()}] >> {msg}")

    @staticmethod
    def is_file_readable(filepath: str) -> bool:
        """
        * Проверка доступности файла для чтения
        *
        * @param filepath Имя файла
        * @return True - файл доступа; False - файл недоступен
        """
        if (
            (not os.path.exists(filepath))
            or (not os.path.isfile(filepath))
            or (not os.access(filepath, os.R_OK))
        ):
            return False
        else:
            return True

    @staticmethod
    def get_local_ip_addresses():
        """
        * Список IP-адресов для сетевых интерфейсов
        *
        * @return Массив IP-адресов
        """
        ip_addresses = []
        hostname: str = socket.gethostname()
        try:
            ip_addresses = socket.gethostbyname_ex(hostname)[2] # Получаем список IP-адресов
        except socket.gaierror:
            pass
        return ip_addresses

    @staticmethod
    def get_username() -> str:
        """
        * Возвращает имя пользователя, работающего под Windows или Linux
        *
        * @return Имя пользователя
        """
        if sys.platform == "win32":
            return os.environ.get("USERNAME")
        else:
            return os.environ.get("USER")

    @staticmethod
    def get_running_processes():
        """
        * Список имён работающих процессов
        *
        * @return Массив имён работающих процессов
        """
        process_names = []
        for process in psutil.process_iter(['pid', 'name']): # Итерируемся по процессам
            try:
                process_names.append(process.info['name']) # Добавляем имя процесса в список
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass # игнорируем ошибки, если процесс исчез, или нет прав доступа
        return process_names

    @staticmethod
    def get_system_properties():
        """
        * Получение характеристик операционной системы
        *
        * @return Кортеж с характеристиками операционной системы
        """
        os_name: str = platform.system()
        os_version: str = platform.version()
        os_release: str = platform.release()
        memory = psutil.virtual_memory()
        total_memory: str = f'{memory.total / (1024**3):.2f} ГБ'
        used_memory: str = f'{memory.used / (1024**3):.2f} ГБ'
        available_memory: str = f'{memory.available / (1024**3):.2f} ГБ'
        percent_memory: str = f'{memory.percent}%'
        return os_name, os_version, os_release, total_memory, used_memory, available_memory, percent_memory

    @staticmethod
    def get_phrase_outta_file(filepath: str, codepage: str) -> str:
        """
        * Случайная строка из текстового файла
        *
        * @param filepath Имя текстового файла
        * @param codepage Кодировка текстового файла
        * @return Случайная строка из текстового файла
        """
        MAX_LINES_TO_READ: int = 1000  # ограничение на количество строк для чтения
        if not Miscellaneous.is_file_readable(filepath):
            return ""  # возвращаем пустую строку, если файл недоступен
        try:
            with open(filepath, "r", encoding=codepage) as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= MAX_LINES_TO_READ:
                        break
                    lines.append(line.strip())
            lines = [line for line in lines if line]  # удаляем пустые строки из списка
            if not lines:
                return ""
            random_phrase: str = random.choice(lines)  # выбираем случайную строку
            return random_phrase
        except Exception as e:
            return ""

    @staticmethod
    def get_url(url: str, http_proxy: str = "", https_proxy: str = "") -> Any:
        """
        * Запрашивает URL с использованием прокси-серверов (если указаны)
        *
        * @param url URL для запроса
        * @param http_proxy HTTP прокси
        * @param https_proxy HTTPS прокси
        * @return Список строк
        """
        proxies: Any = {}
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy
        try:
            response: requests.Response = requests.get(url, proxies=proxies, stream=True)
            response.raise_for_status()
            lines = [line.decode(response.encoding, errors='ignore') for line in response.iter_lines(decode_unicode=False, delimiter=b'\n')]
            return lines
        except requests.exceptions.RequestException:
            return []  # Error during request
        except Exception:
            return [] # An unexpected error

    @staticmethod
    def get_delta_time(p_seconds: int) -> str:
        """
        * Вычисление времени по дельте относительно текущего времени
        *
        * @param p_seconds Целочисленное количество секунд
        * @return Строка времени в формате "hh24:mi:ss"
        """
        my_datetime: datetime = datetime.today()
        my_datetime_sec: datetime = my_datetime + timedelta(seconds = p_seconds)
        return my_datetime_sec.time().strftime("%H:%M:%S")

    @staticmethod
    def run_command(command: str, output_file: str = None) -> int:
        try:
            output_lines = []
            process = subprocess.Popen(
                command,
                stdout = subprocess.PIPE,  # Перехватываем стандартный вывод
                stderr = subprocess.PIPE,  # Перехватываем стандартный вывод ошибок (по желанию)
                text = True  # Чтобы получать вывод в виде строк, а не байтов
            )
            stdout, stderr = process.communicate()  # Получаем вывод и ошибки
            if output_file is not None:
                with open(output_file, "w") as f:
                    f.write(stdout)
            else:
                print(stdout)
                output_lines = stdout.splitlines() # Разделяем вывод на строки
            if stderr is not None:
                print(f"Ошибки:\n{stderr}")  # Выводим ошибки, если они есть
            return output_lines, process.returncode
        except FileNotFoundError:
            print(f"Ошибка: Команда '{command[0]}' не найдена.")
            return output_lines, 1
        except PermissionError:
            print("Ошибка доступа к файлу.")
            return output_lines, 2
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return output_lines, 3

    @staticmethod
    def run_command_from_string(command_string: str, output_file: str = None) -> int:
        if not "".__eq__(command_string):
            try:
                command = shlex.split(command_string)
                return Miscellaneous.run_command(command, output_file)
            except Exception as e:
                print(f"Ошибка разбора команды: {e}")
                return [], 1
        else:
            return 0

    @staticmethod
    def is_dangerous_command(p_cmd: str) -> bool:
        """
        * Признак того, что команда содержит опасные элементы
        *
        * @param p_cmd Исходная команда
        * @return True - содержит опасные элементы; False - не содержит опасные элементы
        """
        DANGEROUS_COMMANDS = [
            "rm", "rd", "rmdir", "del",
            "erase", "format", "dd", "mkfs",
            "fdisk", "cp", "mv", "chmod",
            "chown", "attrib", "tar", "zip",
            "unzip", "rar", "unrar", "parted",
            "tune2fs", "nano", "vi", "vim",
            "edit", "mc", "sys", "service",
            "systemctl", "poweroff", "reboot", "halt",
            "su", "sudo", "logout", "kill", "pkill",
            "touch", "copy", "ren", ".py",
            ".java", ".rb", "configure", "make",
            "cmake", ".cmd", ".sh", ".bat", ".exe",
            ".com", "telnet", "irssi", "ssh",
            "read", "choice", "set", "export",
            "checkinstall"
        ]
        p_cmd = p_cmd.lower().strip()
        cmd_parts = shlex.split(p_cmd)
        for command in DANGEROUS_COMMANDS:
            if command in cmd_parts:
                return True
        return False

    @staticmethod
    def read_rss_feed(feed_url: str, lim: int = 10, proxy_type: str = None, proxy_server: str = None):
        """
        * Чтение новостной ленты RSS
        *
        * @param feed_url URL для RSS
        * @param lim Максимальное количество новостных строк
        * @param proxy_type Тип proxy-сервера
        * @param proxy_server URL proxy-сервера
        * @return Заголовки и ссылки новостей RSS
        """
        titles = []
        links = []
        if not "".__eq__(feed_url):
            isThroughProxy: bool = False
            proxy_handler: ProxyHandler = None
            if proxy_type is not None and proxy_server is not None:
                proxy_handler = ProxyHandler({proxy_type: proxy_server})
                isThroughProxy = True
            feed: FeedParserDict = feedparser.parse(feed_url) if not isThroughProxy else feedparser.parse(feed_url, handlers=[proxy_handler])
            if not feed.bozo: # условие, когда нет ошибок в RSS
                titles.append(feed.feed.title) # Feed Title
                links.append(feed.feed.link) # Feed Link
                for entry in feed.entries[:10]: # display only the latest 10 entries
                    titles.append(entry.title)
                    links.append(entry.link)
        return titles, links

    @staticmethod
    def is_valid_email(p_email: str) -> bool:
        """
        * Проверка корректности адреса e-mail
        * Адрес электронной почты должен соответствовать стандарту RFC 5322
        * (Internet Message Format).
        * http://www.ietf.org/rfc/rfc5322.txt
        *
        * @param p_email Адрес электронной почты (e-mail)
        * @return True - адрес электронной почты в порядке; False - в адресе электронной почты есть ошибки
        """
        is_valid: bool = False
        if not "".__eq__(p_email):
            is_valid = re.compile(r"^\S+@\S+\.\S+$").match(p_email) is not None
        return is_valid

    @staticmethod
    def send_email(p_host: str, p_port: int, p_subject: str, p_text: str, p_from: str, p_to: str, p_tls: bool = False, p_user: str = None, p_password: str = None) -> bool:
        """
        * Отправка e-mail
        *
        * @param p_host Хост SMTP-сервера
        * @param p_port Порт SMTP-сервера
        * @param p_subject Тема письма
        * @param p_text Текст письма (MIME-тип: plain/text)
        * @param p_from Адрес электронной почты отправителя (т.е. "от кого")
        * @param p_to Адрес электронной почты получателя (т.е. "кому")
        * @param p_tls Признак "SSL/TLS" для SMTP-сервера (по умолчанию - нет)
        * @param p_user Логин для SMTP-сервера с аутентификацией (не заполнять, если сервер без аутентификации)
        * @param p_password Пароль для SMTP-сервера с аутентификацией (не заполнять, если сервер без аутентификации)
        * @return True - нет ошибок при отправке; False - есть ошибки при отправке
        """
        SMTP_TIMEOUT: float = 10 # через сколько секунд считать, что сервер не отвечает
        is_sent: bool = False
        if (
            not "".__eq__(p_host)
            and 1 <= p_port <= 65534
            and not "".__eq__(p_subject)
            and not "".__eq__(p_text)
            and Miscellaneous.is_valid_email(p_from)
            and Miscellaneous.is_valid_email(p_to)
        ):
            msg: EmailMessage = EmailMessage()
            msg.set_content(p_text)
            msg["Subject"] = p_subject
            msg["From"] = p_from
            msg["To"] = p_to
            is_smtp_ok: bool = True
            s: SMTP = None
            s_ssl: SMTP_SSL = None
            try:
                if p_tls:
                    s_ssl = SMTP_SSL(p_host, p_port, timeout = SMTP_TIMEOUT)
                else:
                    s = SMTP(p_host, p_port, timeout = SMTP_TIMEOUT)
                if p_tls:
                    s_ssl.ehlo()
                else:
                    s.ehlo()
                if p_user is not None and p_password is not None:
                    if p_tls:
                        s_ssl.login(p_user, p_password)
                    else:
                        s.login(p_user, p_password)
                if p_tls:
                    s_ssl.send_message(msg)
                else:
                    s.send_message(msg)
            except SMTPException:
                is_smtp_ok = False
            finally:
                if s is not None:
                    s.quit()
                if s_ssl is not None:
                    s_ssl.quit()
            is_sent = is_smtp_ok
        return is_sent
