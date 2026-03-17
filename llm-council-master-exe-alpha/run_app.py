import multiprocessing
import uvicorn
import webview
import time
import socket
import sys
import os
from backend.main import app

# Fix for PyInstaller windowed mode where stdout/stderr might be None
def redirect_outputs():
    if sys.stdout is None or isinstance(sys.stdout, (type(None),)):
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None or isinstance(sys.stderr, (type(None),)):
        sys.stderr = open(os.devnull, "w")

def start_server():
    redirect_outputs()
    # Запускаем сервер FastAPI
    # Используем логгер "warning" чтобы не мусорить
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning", access_log=False)

def wait_for_server(port, timeout=15):
    # Ожидаем, пока сервер не поднимется
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

if __name__ == '__main__':
    # Обязательно для многопроцессности в PyInstaller на Windows
    multiprocessing.freeze_support()
    
    # Редирект в основном процессе
    redirect_outputs()
    
    # Запускаем FastAPI в отдельном фоновом процессе
    server_process = multiprocessing.Process(target=start_server)
    server_process.daemon = True
    server_process.start()
    
    try:
        # Ждём, пока сервер будет готов принимать запросы
        if wait_for_server(8001):
            # Открываем "встроенный" браузер
            # debug=False убирает инструменты разработчика в окне
            window = webview.create_window(
                'LLM Council', 
                'http://127.0.0.1:8001', 
                width=1280, 
                height=850,
                min_size=(800, 600)
            )
            webview.start(debug=False)
        else:
            print("Не удалось запустить локальный сервер :(")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # При закрытии окна или ошибке завершаем сервер
        if server_process.is_alive():
            server_process.terminate()
            server_process.join(timeout=2)
        sys.exit(0)
