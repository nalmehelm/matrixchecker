import webview
import time
import threading
import os
import sys
from scanner.core import ScannerAPI

def get_resource_path(relative_path):
    """Получить путь к ресурсам (работает и в .exe и в .py)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    # Создаём экземпляр API для связи с фронтендом
    api = ScannerAPI()
    
    # Проверяем обновления при запуске
    def check_updates_on_startup():
        time.sleep(2)  # Ждем загрузки интерфейса
        update_info = api.updater.check_for_updates()
        
        if update_info.get('available'):
            api.log('info', f'New version {update_info["version"]} is available!')
            if api.window:
                api.window.evaluate_js(
                    f'showUpdateNotification("{update_info["version"]}")'
                )
    
    threading.Thread(target=check_updates_on_startup, daemon=True).start()
    
    # Путь к HTML файлу
    html_path = get_resource_path('web/index.html')
    
    # Проверяем существование файла
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        sys.exit(1)
    
    # Создаём окно приложения
    window = webview.create_window(
        title='Matrix Scanner - Advanced Threat Detection System',
        url=html_path,
        js_api=api,
        width=1400,
        height=900,
        min_size=(1000, 700),
        resizable=True,
        frameless=False,
        easy_drag=False,
        background_color='#000000'
    )
    
    # Сохраняем ссылку на окно в API для обновлений UI
    api.set_window(window)
    
    # Запускаем приложение
    webview.start(debug=False)

if __name__ == '__main__':
    main()