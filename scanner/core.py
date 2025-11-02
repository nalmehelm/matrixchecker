import os
from updater import AutoUpdater
import time
import hashlib
import random
import threading
import psutil
import webview
from pathlib import Path
from typing import List, Dict, Any, Optional
import platform
import zipfile

class ScannerAPI:
    """API для поиска читов Minecraft"""
    
    
    def __init__(self):
        self.window = None
        self.scanning = False
        self.scan_thread = None
        self.files_to_scan = []
        self.found_threats = []
        self.stats = {
            'scanned': 0,
            'threats': 0,
            'clean': 0,
            'start_time': None
        }
        
        
        # Список известных читов для Minecraft (точные названия)
        self.minecraft_cheats = {
            # Популярные читы
            'liquidbounce': 'LiquidBounce',
            'nursultan': 'Nursultan',
            'excellent': 'Excellent',
            'expensive': 'Expensive',
            'delta': 'Delta',
            'wexside': 'Wexside',
            'celestial': 'Celestial',
            'wurst': 'Wurst',
            'impact': 'Impact',
            'meteor': 'Meteor Client',
            
            # Другие известные читы
            'aristois': 'Aristois',
            'sigma': 'Sigma',
            'flux': 'Flux',
            'lambda': 'Lambda',
            'inertia': 'Inertia',
            'ares': 'Ares',
            'wolfram': 'Wolfram',
            'pyro': 'Pyro',
            'rusherhack': 'RusherHack',
            'future': 'Future',
            'konas': 'Konas',
            'salhack': 'SalHack',
            'phobos': 'Phobos',
            'kamihack': 'KamiHack',
            'creepy salhack': 'Creepy SalHack',
            'earthhack': 'EarthHack',
            'gamesense': 'GameSense',
            'kami blue': 'Kami Blue',
            'zenith': 'Zenith',
            'abyss': 'Abyss',
            'bleachhack': 'BleachHack',
            'valhalla': 'Valhalla',
            'devil': 'Devil',
            'xulu': 'Xulu',
            'remix': 'Remix',
            'vonware': 'Vonware',
            'thunderhack': 'ThunderHack',
            'banana': 'Banana',
            'catalyst': 'Catalyst',
            'backdoored': 'Backdoored',
            'forgehax': 'ForgeHax',
            'huzuni': 'Huzuni',
            'nodus': 'Nodus',
            'wizardhax': 'WizardHax',
            'xray': 'XRay',
            'mineplex': 'Mineplex',
            'vape': 'Vape',
            'entropy': 'Entropy',
            'azura': 'Azura',
            'atlas': 'Atlas',
            'vertex': 'Vertex',
            'astolfo': 'Astolfo',
            'exhibition': 'Exhibition',
            'rise': 'Rise',
            'novoline': 'Novoline',
            'suicide': 'Suicide',
            'jello': 'Jello',
            'winterware': 'Winterware',
            'crypt': 'Crypt',
            'moon': 'Moon',
            'slinky': 'Slinky',
            'gopro': 'GoPro',
            'lblc': 'LBLC',
            'vestige': 'Vestige',
            'tenacity': 'Tenacity',
            'eject': 'Eject',
            'rockstar': 'Rockstar',
            'drip': 'Drip',
            'shield': 'Shield',
            'akrien': 'Akrien',
            'spicy': 'Spicy',
            'augustus': 'Augustus',
        }
        
        # Расширения файлов читов
        self.cheat_extensions = ['.jar', '.exe']
        
        # Директории для сканирования ВСЕЙ СИСТЕМЫ
        self.scan_directories = self._get_all_system_directories()
        
        # Список процессов читов для завершения
        self.threat_processes = {}
        self.updater = AutoUpdater(
        current_version='2.4.1',
        github_repo='nalmehelm/matrixchecker'  # ЗАМЕНИТЕ на ваш репозиторий
    )
        self.update_available = None

    def check_updates(self) -> Dict[str, Any]:
        """Проверить наличие обновлений"""
        try:
            self.log('info', 'Checking for updates...')
            update_info = self.updater.check_for_updates()
            
            if update_info.get('available'):
                self.update_available = update_info
                self.log('info', f'New version available: {update_info["version"]}')
                return {
                    'success': True,
                    'available': True,
                    'version': update_info['version'],
                    'changelog': update_info['changelog'],
                    'release_name': update_info['release_name']
                }
            elif update_info.get('error'):
                self.log('warning', f'Update check failed: {update_info["error"]}')
                return {
                    'success': False,
                    'error': update_info['error']
                }
            else:
                self.log('info', 'You are using the latest version')
                return {
                    'success': True,
                    'available': False,
                    'message': 'No updates available'
                }
                
        except Exception as e:
            self.log('error', f'Failed to check updates: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }

    def download_update(self) -> Dict[str, Any]:
        """Скачать доступное обновление"""
        if not self.update_available or not self.update_available.get('available'):
            return {
                'success': False,
                'message': 'No update available to download'
            }
        
        try:
            download_url = self.update_available['download_url']
            
            self.log('info', f'Downloading update from {download_url}')
            
            def progress_callback(progress, downloaded, total):
                if self.window:
                    self.window.evaluate_js(
                        f'updateDownloadProgress({progress:.1f}, {downloaded}, {total})'
                    )
            
            file_path = self.updater.download_update(download_url, progress_callback)
            
            if file_path and self.updater.verify_download(file_path):
                self.log('info', f'Update downloaded successfully: {file_path}')
                return {
                    'success': True,
                    'file_path': file_path,
                    'message': 'Update downloaded successfully'
                }
            else:
                self.log('error', 'Failed to download or verify update')
                return {
                    'success': False,
                    'message': 'Download failed or file corrupted'
                }
                
        except Exception as e:
            self.log('error', f'Error downloading update: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }

    def install_update(self, file_path: str) -> Dict[str, Any]:
        """Установить скачанное обновление"""
        try:
            self.log('info', 'Installing update...')
            
            if self.updater.install_update(file_path):
                self.log('info', 'Update will be installed on restart')
                return {
                    'success': True,
                    'message': 'Update installed. Restarting application...'
                }
            else:
                self.log('error', 'Failed to install update')
                return {
                    'success': False,
                    'message': 'Installation failed'
                }
                
        except Exception as e:
            self.log('error', f'Error installing update: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_all_system_directories(self) -> List[str]:
        """Получить ВСЕ диски и основные директории для полного сканирования"""
        directories = []
        system = platform.system()
        
        if system == 'Windows':
            # Получаем ВСЕ доступные диски
            drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
            
            self.log('info', f'Found {len(drives)} drive(s): {", ".join(drives)}')
            
            # Добавляем корни всех дисков для полного сканирования
            directories.extend(drives)
            
        elif system == 'Linux':
            # Для Linux сканируем от корня
            directories.append('/')
            
        elif system == 'Darwin':  # macOS
            # Для macOS сканируем основные директории
            directories.extend(['/', '/Users', '/Applications'])
        
        return directories
    
    def set_window(self, window):
        """Сохранить ссылку на окно для обновления UI"""
        self.window = window
    
    def log(self, level: str, message: str):
        """Отправить лог в консоль UI"""
        if self.window:
            message = message.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            self.window.evaluate_js(f'addLog("{level}", "{message}")')
    
    def update_stats(self):
        """Обновить статистику в UI"""
        if self.window:
            self.window.evaluate_js(
                f'updateStats({self.stats["scanned"]}, {self.stats["threats"]}, {self.stats["clean"]})'
            )
    
    def update_progress(self, current: int, total: int, file_name: str):
        """Обновить прогресс-бар"""
        if self.window:
            percent = (current / total * 100) if total > 0 else 0
            file_name = file_name.replace('\\', '\\\\').replace('"', '\\"')
            self.window.evaluate_js(f'updateProgress({percent}, "{file_name}")')
    
    def update_timer(self):
        """Обновить таймер сканирования"""
        if self.window and self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            self.window.evaluate_js(f'updateTimer({elapsed})')
    
    def add_file_to_list(self, file_data: Dict[str, Any]):
        """Добавить файл в список UI"""
        if self.window:
            import json
            file_json = json.dumps(file_data)
            self.window.evaluate_js(f'addFileToList({file_json})')
    
    def update_file_status(self, file_id: str, status: str, result: Optional[Dict] = None):
        """Обновить статус файла в UI"""
        if self.window:
            import json
            result_json = json.dumps(result) if result else 'null'
            self.window.evaluate_js(f'updateFileStatus("{file_id}", "{status}", {result_json})')
    
    def is_minecraft_cheat(self, file_path: str, file_name: str) -> tuple:
        """Проверить, является ли файл читом Minecraft по названию"""
        file_name_lower = file_name.lower()
        
        # Проверяем расширение
        if not any(file_name_lower.endswith(ext) for ext in self.cheat_extensions):
            return False, None
        
        # Убираем расширение для проверки
        name_without_ext = os.path.splitext(file_name_lower)[0]
        
        # Проверяем точное совпадение с известными читами
        for cheat_key, cheat_name in self.minecraft_cheats.items():
            # Проверяем точное совпадение названия
            if cheat_key == name_without_ext or cheat_key in name_without_ext:
                return True, cheat_name
            
            # Проверяем вариации с версиями (например, liquidbounce-1.8.9)
            if name_without_ext.startswith(cheat_key + '-') or \
               name_without_ext.startswith(cheat_key + '_') or \
               name_without_ext.startswith(cheat_key + ' '):
                return True, cheat_name
        
        return False, None
    
    def check_jar_manifest(self, file_path: str) -> Optional[str]:
        """Проверить манифест JAR файла на наличие маркеров читов"""
        try:
            if not file_path.lower().endswith('.jar'):
                return None
            
            with zipfile.ZipFile(file_path, 'r') as jar:
                # Проверяем манифест
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest = jar.read('META-INF/MANIFEST.MF').decode('utf-8', errors='ignore')
                    manifest_lower = manifest.lower()
                    
                    for cheat_key, cheat_name in self.minecraft_cheats.items():
                        if cheat_key in manifest_lower:
                            return cheat_name
                
                # Проверяем названия файлов внутри JAR
                for file in jar.namelist():
                    file_lower = file.lower()
                    for cheat_key, cheat_name in self.minecraft_cheats.items():
                        if cheat_key in file_lower:
                            return cheat_name
        except:
            pass
        
        return None
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Сканировать один файл"""
        try:
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            
            # Вычисляем SHA256 хеш
            sha256_hash = "calculating..."
            try:
                with open(file_path, 'rb') as f:
                    content = f.read(min(file_size, 1024 * 1024))  # Первый 1MB
                    sha256_hash = hashlib.sha256(content).hexdigest()
            except:
                pass
            
            file_name = os.path.basename(file_path)
            
            # Проверяем по названию
            is_threat, threat_type = self.is_minecraft_cheat(file_path, file_name)
            
            # Если не обнаружено по названию, проверяем содержимое JAR
            if not is_threat and file_path.lower().endswith('.jar'):
                jar_threat = self.check_jar_manifest(file_path)
                if jar_threat:
                    is_threat = True
                    threat_type = jar_threat
            
            # Проверяем, запущен ли процесс
            is_running = False
            if is_threat:
                is_running = self.is_process_running(file_path)
            
            threat_level = random.randint(2, 3) if is_threat else 0
            
            return {
                'path': file_path,
                'name': file_name,
                'size': file_size,
                'hash': sha256_hash,
                'isThreat': is_threat,
                'threatLevel': threat_level,
                'threatType': threat_type if is_threat else None,
                'scanDate': time.time(),
                'isRunning': is_running
            }
            
        except Exception as e:
            self.log('error', f'Error scanning {file_path}: {str(e)}')
            raise
    
    def is_process_running(self, file_path: str) -> bool:
        """Проверить, запущен ли процесс из этого файла"""
        try:
            file_name = os.path.basename(file_path)
            
            # Для .jar файлов проверяем процессы Java
            if file_path.lower().endswith('.jar'):
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if cmdline and any(file_name in cmd for cmd in cmdline):
                            if file_path not in self.threat_processes:
                                self.threat_processes[file_path] = []
                            self.threat_processes[file_path].append(proc.pid)
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            # Для .exe файлов проверяем по имени
            elif file_path.lower().endswith('.exe'):
                file_name_lower = file_name.lower()
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        proc_name = proc.info['name']
                        if proc_name and proc_name.lower() == file_name_lower:
                            if file_path not in self.threat_processes:
                                self.threat_processes[file_path] = []
                            self.threat_processes[file_path].append(proc.pid)
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
        except Exception as e:
            pass
        
        return False
    
    def scan_directory_recursively(self, root_path: str, file_count_ref: list, last_update_time: list):
        """Рекурсивное сканирование директории с обновлением прогресса"""
        
        # Папки которые нужно пропустить для ускорения
        skip_dirs = {
            'Windows', 'WinSxS', '$Recycle.Bin', 'System Volume Information',
            'ProgramData', 'AppData\\Local\\Temp', 'node_modules', '.git',
            'Program Files\\Windows', 'Program Files (x86)\\Windows'
        }
        
        try:
            for root, dirs, files in os.walk(root_path):
                # Фильтруем директории
                dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_dirs)]
                
                for file in files:
                    if not self.scanning:
                        return
                    
                    # Проверяем только .jar и .exe файлы
                    if any(file.lower().endswith(ext) for ext in self.cheat_extensions):
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Проверяем файл
                            result = self.scan_file(file_path)
                            
                            self.stats['scanned'] += 1
                            file_count_ref[0] += 1
                            
                            if result['isThreat']:
                                self.stats['threats'] += 1
                                self.found_threats.append(result)
                                
                                # Добавляем в UI только угрозы
                                file_id = hashlib.md5(file_path.encode()).hexdigest()
                                file_data = {
                                    'id': file_id,
                                    'path': file_path,
                                    'name': file,
                                    'status': 'threat'
                                }
                                self.add_file_to_list(file_data)
                                self.update_file_status(file_id, 'threat', result)
                                
                                status_msg = f'MINECRAFT CHEAT FOUND: {result["threatType"]} ({result["name"]})'
                                if result.get('isRunning'):
                                    status_msg += ' [RUNNING]'
                                self.log('error', status_msg)
                            else:
                                self.stats['clean'] += 1
                            
                            # Обновляем UI каждые 100 файлов или каждую секунду
                            current_time = time.time()
                            if file_count_ref[0] % 100 == 0 or (current_time - last_update_time[0] >= 1.0):
                                self.update_stats()
                                self.update_timer()
                                self.update_progress(
                                    file_count_ref[0],
                                    file_count_ref[0] + 1000,  # Примерное общее количество
                                    f'Scanning: {file}'
                                )
                                last_update_time[0] = current_time
                            
                        except Exception as e:
                            # Тихо пропускаем файлы с ошибками доступа
                            pass
                
        except PermissionError:
            # Пропускаем директории без доступа
            pass
        except Exception as e:
            pass
    
    def start_scan(self, scan_mode: str = 'quick') -> Dict[str, Any]:
        """Запустить сканирование всей системы"""
        if self.scanning:
            return {'success': False, 'message': 'Scan already in progress'}
        
        self.scanning = True
        self.found_threats = []
        self.threat_processes = {}
        self.stats = {
            'scanned': 0,
            'threats': 0,
            'clean': 0,
            'start_time': time.time()
        }
        
        # Запускаем сканирование в отдельном потоке
        self.scan_thread = threading.Thread(target=self._scan_worker, args=(scan_mode,))
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
        self.log('info', f'Starting FULL SYSTEM scan in {scan_mode} mode...')
        self.log('info', f'Scanning entire system for Minecraft cheats...')
        self.log('info', f'This may take a while. Searching for: {", ".join(list(self.minecraft_cheats.values())[:10])}...')
        
        return {'success': True, 'message': 'Scan started'}
    
    def _scan_worker(self, scan_mode: str):
        """Рабочий поток для сканирования всей системы"""
        self.log('info', 'Starting deep system scan...')
        
        file_count_ref = [0]  # Счетчик файлов (используем список для передачи по ссылке)
        last_update_time = [time.time()]
        
        # Сканируем каждую директорию/диск
        for directory in self.scan_directories:
            if not self.scanning:
                break
            
            dir_name = os.path.basename(directory) if os.path.basename(directory) else directory
            self.log('info', f'Scanning: {directory}')
            
            # Рекурсивное сканирование
            self.scan_directory_recursively(directory, file_count_ref, last_update_time)
        
        # Завершение сканирования
        self._finish_scan()
    
    def _finish_scan(self):
        """Завершить сканирование"""
        self.scanning = False
        
        if self.stats['start_time']:
            elapsed_time = time.time() - self.stats['start_time']
            self.log('info', f'=== SCAN COMPLETE ===')
            self.log('info', f'Time: {elapsed_time:.1f}s')
            self.log('info', f'Total files scanned: {self.stats["scanned"]}')
            self.log('info', f'Minecraft cheats found: {self.stats["threats"]}')
            self.log('info', f'Clean files: {self.stats["clean"]}')
        
        # Обновляем финальную статистику
        self.update_stats()
        self.update_timer()
        
        if self.window:
            self.window.evaluate_js('onScanComplete()')
    
    def stop_scan(self) -> Dict[str, Any]:
        """Остановить сканирование"""
        if not self.scanning:
            return {'success': False, 'message': 'No scan in progress'}
        
        self.scanning = False
        self.log('warning', 'Scan stopped by user')
        
        return {'success': True, 'message': 'Scan stopped'}
    
    def clear_threats(self) -> Dict[str, Any]:
        """Удалить все обнаруженные угрозы и закрыть процессы"""
        if not self.found_threats:
            return {'success': False, 'message': 'No threats to clear'}
        
        deleted = 0
        failed = 0
        processes_killed = 0
        
        self.log('info', f'Clearing {len(self.found_threats)} Minecraft cheat(s)...')
        
        for threat in self.found_threats[:]:
            file_path = threat['path']
            
            try:
                # Завершаем процесс, если запущен
                if file_path in self.threat_processes:
                    for pid in self.threat_processes[file_path]:
                        try:
                            proc = psutil.Process(pid)
                            proc_name = proc.name()
                            proc.kill()
                            proc.wait(timeout=5)
                            processes_killed += 1
                            self.log('warning', f'Killed process: {proc_name} (PID: {pid})')
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                            self.log('error', f'Failed to kill process {pid}: {str(e)}')
                
                time.sleep(0.5)
                
                # Удаляем файл
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.log('info', f'Deleted: {threat["threatType"]} - {threat["name"]}')
                    deleted += 1
                    self.found_threats.remove(threat)
                    
            except PermissionError:
                self.log('error', f'Permission denied: {threat["name"]} (File may be in use or protected)')
                failed += 1
            except Exception as e:
                self.log('error', f'Failed to delete {threat["name"]}: {str(e)}')
                failed += 1
        
        # Обновляем статистику
        self.stats['threats'] = len(self.found_threats)
        self.update_stats()
        
        message = f'Cleared {deleted} cheat(s), killed {processes_killed} process(es)'
        if failed > 0:
            message += f', {failed} failed'
        
        self.log('info', message)
        
        return {
            'success': True,
            'deleted': deleted,
            'processes_killed': processes_killed,
            'failed': failed,
            'message': message
        }
    
    def quarantine_file(self, file_path: str) -> Dict[str, Any]:
        """Поместить файл в карантин"""
        try:
            # Завершаем процесс если запущен
            if file_path in self.threat_processes:
                for pid in self.threat_processes[file_path]:
                    try:
                        proc = psutil.Process(pid)
                        proc.kill()
                        proc.wait(timeout=5)
                    except:
                        pass
            
            time.sleep(0.5)
            
            # Создаём папку карантина
            quarantine_dir = os.path.join(os.path.expanduser('~'), '.matrix_scanner', 'quarantine')
            os.makedirs(quarantine_dir, exist_ok=True)
            
            # Перемещаем файл
            file_name = os.path.basename(file_path)
            timestamp = int(time.time())
            quarantine_path = os.path.join(quarantine_dir, f'{timestamp}_{file_name}.quar')
            
            import shutil
            shutil.move(file_path, quarantine_path)
            
            self.log('info', f'Quarantined: {file_name}')
            
            return {
                'success': True,
                'quarantine_path': quarantine_path,
                'message': 'File moved to quarantine'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to quarantine: {str(e)}'
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Удалить файл и завершить процесс"""
        try:
            # Завершаем процесс если запущен
            if file_path in self.threat_processes:
                for pid in self.threat_processes[file_path]:
                    try:
                        proc = psutil.Process(pid)
                        proc_name = proc.name()
                        proc.kill()
                        proc.wait(timeout=5)
                        self.log('warning', f'Killed process: {proc_name}')
                    except:
                        pass
            
            time.sleep(0.5)
            
            # Удаляем файл
            if os.path.exists(file_path):
                os.remove(file_path)
                self.log('info', f'Deleted: {os.path.basename(file_path)}')
                
                return {
                    'success': True,
                    'message': 'File deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'File not found'
                }
                
        except PermissionError:
            return {
                'success': False,
                'message': 'Permission denied - file may be protected or in use'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to delete: {str(e)}'
            }
    
    def export_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Экспортировать отчёт"""
        try:
            if self.window:
                file_path = self.window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    save_filename=f'minecraft_cheat_scan_{int(time.time())}.json',
                    file_types=('JSON Files (*.json)', 'Text Files (*.txt)')
                )
                
                if file_path:
                    import json
                    
                    # Добавляем информацию о найденных угрозах
                    report_data['threats'] = self.found_threats
                    report_data['scan_directories'] = self.scan_directories
                    report_data['known_cheats'] = list(self.minecraft_cheats.values())
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(report_data, f, indent=2, ensure_ascii=False)
                    
                    self.log('info', f'Report exported to: {file_path}')
                    
                    return {
                        'success': True,
                        'path': file_path
                    }
            
            return {
                'success': False,
                'message': 'Export cancelled'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to export: {str(e)}'
            }
    
    def clear_list(self) -> Dict[str, Any]:
        """Очистить список файлов"""
        self.found_threats.clear()
        self.threat_processes.clear()
        self.stats = {
            'scanned': 0,
            'threats': 0,
            'clean': 0,
            'start_time': None
        }
        
        self.log('info', 'Results cleared')
        
        return {'success': True, 'message': 'List cleared'}