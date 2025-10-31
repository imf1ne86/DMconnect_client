"""
* Класс для обмена данными с сервером DMconnect
* *************************
* Документацию по протоколу DMconnect можно изучить на
* сайте: https://dmconnectspec.w10.site
*
* @author Ефремов А. В., 30.10.2025
"""

from typing import Optional, Deque
from socket import socket, AF_INET, SOCK_STREAM
import errno
from threading import Thread
from time import sleep
from collections import deque

CODEPAGE: str = "utf-8" # используемая кодировка
PING_CMD: str = "/" # команда "ping" для сервера DMconnect
QUIT_CMD: str = "" # команда "quit" для сервера DMconnect
DELAY: float = 3 # время задержки (в секундах) при обмене данными с сервером

class DMconn:

    sock: Optional[socket] = None
    th_keepalive: Optional[Thread] = None
    th_receive_data: Optional[Thread] = None
    msg_buffer: Deque[str] = deque(maxlen = 1000) # буфер для хранения последних 1000 ответов от сервера DMconnect

    def __init__(self, host: str, port: int, user: str, password: str, join_server: str = "general"):
        if not "".__eq__(host) and 1 <= port <= 65534 and not "".__eq__(user) and not "".__eq__(password) and not "".__eq__(join_server):
            self.sock = socket(AF_INET, SOCK_STREAM)
            try:
                self.sock.connect((host, port))
            except Exception:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            if self.sock is not None:
                self.th_keepalive = Thread(target = self.keepalive, daemon = True)
                self.th_keepalive.start()
                self.th_receive_data = Thread(target = self.read, daemon = True)
                self.th_receive_data.start()
                sleep(DELAY)
                self.write(f"/login {user} {password}") # аутентификация
                self.write(f"/join_server {join_server}") # вход на выбранный подсервер

    def keepalive(self) -> None:
        """
        * Соединение keep-alive
        * Метод работает автоматически в режиме многопоточности. Отдельно вызывать
        * его не нужно.
        """
        while self.sock is not None:
            self.write(PING_CMD)

    def close(self) -> None:
        """
        * Закрытие текущего соединения с сервером DMconnect
        """
        if self.sock is not None:
            self.write(QUIT_CMD)
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
            try:
                self.th_keepalive.join()
            except Exception:
                pass
            self.th_keepalive = None
            try:
                self.th_receive_data.join()
            except Exception:
                pass
            self.th_receive_data = None

    def write(self, msg: str) -> None:
        """
        * Отправка на сервер DMconnect сообщения или команды
        *
        * @param msg Текст сообщения или команды
        """
        if self.sock is not None:
            try:
                self.sock.send(msg.strip().encode(CODEPAGE))
                sleep(DELAY)
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError): # фатальная сетевая ошибка - закрываем сокет
                self.close()
            except OSError as e:
                if e.errno in (errno.ENETDOWN, errno.ENETUNREACH, errno.ECONNRESET, errno.ECONNABORTED, errno.ECONNREFUSED): # фатальная сетевая ошибка - закрываем сокет
                    self.close()
            except Exception:
                pass

    def read(self) -> None:
        """
        * Чтение в буфер всех последних сообщений, пришедших от сервера DMconnect
        * Игнорируются ответы по команде "ping", а также сообщение "Unknown command".
        * Метод работает автоматически в режиме многопоточности. Отдельно вызывать
        * его не нужно.
        """
        while self.sock is not None:
            data: Optional[bytes] = None
            try:
                data = self.sock.recv(4096)
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError): # фатальная сетевая ошибка - закрываем сокет
                self.close()
                break
            except OSError as e:
                if e.errno in (errno.ENETDOWN, errno.ENETUNREACH, errno.ECONNRESET, errno.ECONNABORTED, errno.ECONNREFUSED): # фатальная сетевая ошибка - закрываем сокет
                    self.close()
                    break
            except Exception:
                pass
            if not data: # удалённая сторона корректно закрыла соединение (EOF)
                self.close()
                break
            message: str = data.decode(CODEPAGE, errors = "ignore").strip()
            if message in ("*Ping!*", "Unknown command."): # ответ на команду "ping" со стороны сервера DMconnect
                continue
            self.msg_buffer.append(message)
