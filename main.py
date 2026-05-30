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
        # УВЕЛИЧИЛИ ТАЙМАУТ С 1.5 ДО 3.5 СЕКУНД (очень важно для VPN)
        sock = socket.create_connection((ip, int(port)), timeout=3.5)
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
        if ":" in netloc:
            host, port = netloc.split(":")[:2]
            port = re.split(r'[/?]', port)[0]
            
            latency = check_port_and_ping(host, port)
            if latency is not None:
                return (latency, line)
    except:
        pass
    return None

def main():
    print("=== ЗАПУСК ЧЕКЕРА: МАКСИМАЛЬНЫЙ ПОИСК ===")
    checked_servers = []
    seen_configs = set()
    all_lines = []

    # 1. Скачиваем базы
    for url in SOURCES:
        try:
            print(f"Скачиваю базу: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            text = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
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

    # Увеличили лимит с 500 до 3500! Чтобы проверить все доступные в репозиториях.
    if total_found > 3500:
        print(" Серверов очень много! Берем случайные 3500 для проверки...")
        random.shuffle(all_lines)
        all_lines = all_lines[:3500]

    print(f"Запускаю 120 параллельных потоков для проверки {len(all_lines)} конфигураций...")

    # 2. Быстрая проверка пулом. Потоков теперь 120.
    with ThreadPoolExecutor(max_workers=120) as executor:
        futures = [executor.submit(process_line, line) for line in all_lines]
        for i, future in enumerate(as_completed(futures)):
            res = future.result()
            if res is not None:
                checked_servers.append(res)
            if i > 0 and i % 300 == 0:
                print(f" Проверено: {i} / {len(all_lines)}...")

    print(f"Проверка завершена! Найдено живых серверов: {len(checked_servers)}")

    # 3. Сортируем по скорости и отбираем топ-150 лучших
    # Можешь поменять цифру 150 ниже на 100 или 200, если нужно
    checked_servers.sort(key=lambda x: x[0])
    top_fast_servers = checked_servers[:150]
    working_servers = [line for latency, line in top_fast_servers]

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # 4. Формируем файл
    final_lines = [
        "# profile-title: 🌸ZLodeinVPN🌸",
        "# profile-update-interval: 1",
        f"# Последнее обновление: {timestamp} UTC",
        f"# Всего проверено: {len(all_lines)} | Живых: {len(checked_servers)} | Отобрано топ-{len(working_servers)} лучших"
    ]
    final_lines.extend(working_servers)

    with open("cleaned_sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))
    
    print(f" Результат успешно сохранен в cleaned_sub.txt!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("!!! КРИТИЧЕСКИЙ СБОЙ СКРИПТА !!!")
        traceback.print_exc()
        exit(1)
