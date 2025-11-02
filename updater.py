import requests
import os
import sys
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib

class AutoUpdater:
    """Система автоматического обновления программы"""
    
    def __init__(self, current_version: str, github_repo: str):
        self.current_version = current_version
        self.github_repo = "nalmehelm/matrixchecker"  # Формат: "username/repository"
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.update_dir = os.path.join(os.path.expanduser('~'), '.matrix_scanner', 'updates')
        os.makedirs(self.update_dir, exist_ok=True)
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Проверить наличие новой версии"""
        try:
            response = requests.get(self.api_url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].replace('v', '')
                
                if self._compare_versions(latest_version, self.current_version) > 0:
                    return {
                        'available': True,
                        'version': latest_version,
                        'download_url': self._get_download_url(release_data),
                        'changelog': release_data.get('body', 'No changelog available'),
                        'release_name': release_data.get('name', f'Version {latest_version}'),
                        'published_at': release_data.get('published_at', '')
                    }
                else:
                    return {'available': False, 'message': 'You are using the latest version'}
            else:
                return {'available': False, 'error': f'Failed to check updates: HTTP {response.status_code}'}
                
        except requests.RequestException as e:
            return {'available': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'available': False, 'error': f'Error checking updates: {str(e)}'}
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Сравнить две версии. Возвращает 1 если version1 > version2, -1 если меньше, 0 если равны"""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize(version1)
        v2_parts = normalize(version2)
        
        # Дополняем нулями до одинаковой длины
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))
        
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    
    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Получить URL для скачивания подходящего файла"""
        assets = release_data.get('assets', [])
        
        # Определяем платформу
        if sys.platform == 'win32':
            # Ищем .exe файл для Windows
            for asset in assets:
                if asset['name'].endswith('.exe'):
                    return asset['browser_download_url']
        elif sys.platform == 'darwin':
            # Ищем .dmg или .app для macOS
            for asset in assets:
                if asset['name'].endswith(('.dmg', '.app.zip')):
                    return asset['browser_download_url']
        elif sys.platform.startswith('linux'):
            # Ищем .AppImage или исполняемый файл для Linux
            for asset in assets:
                if asset['name'].endswith(('.AppImage', '.tar.gz')):
                    return asset['browser_download_url']
        
        # Если не нашли специфичный файл, возвращаем первый
        return assets[0]['browser_download_url'] if assets else None
    
    def download_update(self, download_url: str, progress_callback=None) -> Optional[str]:
        """Скачать обновление с прогресс-баром"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Получаем имя файла из URL
            filename = download_url.split('/')[-1]
            file_path = os.path.join(self.update_dir, filename)
            
            # Получаем размер файла
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress, downloaded_size, total_size)
            
            return file_path
            
        except Exception as e:
            print(f"Error downloading update: {e}")
            return None
    
    def verify_download(self, file_path: str, expected_hash: Optional[str] = None) -> bool:
        """Проверить целостность скачанного файла"""
        if not os.path.exists(file_path):
            return False
        
        # Проверяем что файл не пустой
        if os.path.getsize(file_path) == 0:
            return False
        
        # Если есть хеш, проверяем его
        if expected_hash:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest() == expected_hash
        
        return True
    
    def install_update(self, file_path: str) -> bool:
        """Установить обновление"""
        try:
            if sys.platform == 'win32':
                return self._install_windows(file_path)
            elif sys.platform == 'darwin':
                return self._install_macos(file_path)
            elif sys.platform.startswith('linux'):
                return self._install_linux(file_path)
            
            return False
            
        except Exception as e:
            print(f"Error installing update: {e}")
            return False
    
    def _install_windows(self, file_path: str) -> bool:
        """Установка на Windows"""
        if file_path.endswith('.exe'):
            # Создаем батник для обновления
            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
            update_script = os.path.join(self.update_dir, 'update.bat')
            
            with open(update_script, 'w') as f:
                f.write(f'@echo off\n')
                f.write(f'echo Updating Matrix Scanner...\n')
                f.write(f'timeout /t 2 /nobreak >nul\n')
                f.write(f'taskkill /F /IM "{os.path.basename(current_exe)}" >nul 2>&1\n')
                f.write(f'timeout /t 1 /nobreak >nul\n')
                f.write(f'copy /Y "{file_path}" "{current_exe}"\n')
                f.write(f'start "" "{current_exe}"\n')
                f.write(f'del "%~f0"\n')
            
            # Запускаем батник и закрываем программу
            subprocess.Popen(['cmd', '/c', update_script], creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        
        return False
    
    def _install_macos(self, file_path: str) -> bool:
        """Установка на macOS"""
        if file_path.endswith('.dmg'):
            # Монтируем DMG и копируем приложение
            subprocess.run(['hdiutil', 'attach', file_path])
            # Здесь нужна дополнительная логика для копирования .app
            return True
        
        return False
    
    def _install_linux(self, file_path: str) -> bool:
        """Установка на Linux"""
        if file_path.endswith('.AppImage'):
            # Заменяем текущий AppImage
            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
            
            # Создаем скрипт обновления
            update_script = os.path.join(self.update_dir, 'update.sh')
            with open(update_script, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('sleep 2\n')
                f.write(f'cp "{file_path}" "{current_exe}"\n')
                f.write(f'chmod +x "{current_exe}"\n')
                f.write(f'"{current_exe}" &\n')
            
            os.chmod(update_script, 0o755)
            subprocess.Popen(['/bin/bash', update_script])
            return True
        
        return False
    
    def cleanup_old_updates(self):
        """Очистить старые файлы обновлений"""
        try:
            if os.path.exists(self.update_dir):
                for file in os.listdir(self.update_dir):
                    file_path = os.path.join(self.update_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up updates: {e}")