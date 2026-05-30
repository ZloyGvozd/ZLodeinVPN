import urllib.request
import socket
import re
import time
import traceback
import random
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCES = [
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta7.txt",
    "https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta6.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"
]

def check_port_and_ping(ip, port):
    try:
        start_time = time.perf_counter()
        # Жестокий таймаут 1.0 сек. Все что медленнее - мусор.
        sock = socket.create_connection((ip, int(port)), timeout=1.0)
        sock.close()
        return time.perf_counter() - start_time
    except:
        return None

def process_line(line):
    line = line.strip()
    if not line or line.startswith("#") or "://" not in line:
        return None
    try:
        clean = line.split('#')[0]
        netloc = urlparse(clean).netloc.split("@")[-1]
        
        # Защита от криво спаршенных строк
        if not netloc:
             return None

        if ":" in netloc:
            # Извлекаем хост и порт, убираем пути и параметры
            host, port = netloc.split(":")[:2]
            port = re.split(r'[/?]', port)[0]
            
            # Базовые проверки на валидность порта
            if not port.isdigit() or int(port) > 65535:
                return None
            
            latency = check_port_and_ping(host, port)
            if latency is not None:
                return (latency, line)
    except:
        pass
    return None

def main():
    print("=== ЗАПУСК СКОРОСТНОГО ЧЕКЕРА (ЖЕСТКАЯ ФИЛЬТРАЦИЯ) ===")
    checked_servers = []
    seen_configs = set()
    all_lines = []

    # 1. Скачиваем базы
    for url in SOURCES:
        try:
            print(f"Скачиваю базу: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            text = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
            count = 0
            for line in text.splitlines():
                line = line.strip()
                if line and "://" in line and not line.startswith("#"):
                    if line not in seen_configs:
                        seen_configs.add(line)
                        all_lines.append(line)
                        count += 1
            print(f"-> Успешно загружено уникальных строк: {count}")
        except Exception as e:
            print(f" Ошибка при скачивании {url}: {e}")

    total_found = len(all_lines)
    print(f" Всего уникальных серверов в базах: {total_found}")

    # УВЕЛИЧИЛИ ПУЛ: Проверяем до 2500 серверов, чтобы найти реальные алмазы
    if total_found > 2500:
        print(" Серверов слишком много! Выбираем 2500 случайных для проверки...")
        random.shuffle(all_lines)
        all_lines = all_lines[:2500]

    print(f"Запускаю 100 параллельных потоков для проверки {len(all_lines)} конфигураций...")

    # 2. Быстрая проверка пулом на 100 потоков
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(process_line, line) for line in all_lines]
        for i, future in enumerate(as_completed(futures)):
            res = future.result()
            if res is not None:
                checked_servers.append(res)
            if i > 0 and i % 500 == 0:
                print(f" Обработано: {i}...")

    print(f"Проверка завершена! Найдено с открытым портом: {len(checked_servers)}")

    # 3. Сортируем по скорости и отбираем топ-100 лучших
    # Большая часть с открытым портом - фейки (CDN или Reality). 
    # Берем только самые быстрые 100 штук (раньше было 300)
    checked_servers.sort(key=lambda x: x[0])
    top_fast_servers = checked_servers[:100]
    working_servers = [line for latency, line in top_fast_servers]

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # 4. Формируем файл
    final_lines = [
        "# profile-title: 🌸ZLodeinVPN🌸",
        "# profile-update-interval: 1",
        f"# Последнее обновление: {timestamp} UTC",
        f"# Проверено: {len(all_lines)} | Отобрано ТОП-100 лучших"
    ]
    final_lines.extend(working_servers)

    with open("cleaned_sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))
    
    print(f" Результат успешно сохранен в cleaned_sub.txt в {timestamp}!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("!!! КРИТИЧЕСКИЙ СБОЙ СКРИПТА !!!")
        traceback.print_exc()
        exit(1)
