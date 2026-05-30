import urllib.request
import socket
import re
import time
import traceback
import random
from urllib.parse import urlparse, parse_qs
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

def is_invalid_ip(ip):
    # Убираем внутренние IP-заглушки и кривые сборки
    invalid_starts = ('127.', '10.', '192.168.', '0.0.', '172.16.')
    if ip.startswith(invalid_starts):
        return True
    return False

def check_socket(ip, port, timeout=2.5):
    # Увеличил таймаут до 2.5 сек, чтобы не отсекать работающие, но задумчивые сервера
    try:
        start_time = time.perf_counter()
        sock = socket.create_connection((ip, int(port)), timeout=timeout)
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
        parsed = urlparse(clean)
        
        # Достаем хост и порт
        netloc = parsed.netloc.split("@")[-1]
        if ":" not in netloc:
            return None
            
        host, port = netloc.split(":")[:2]
        port = re.split(r'[/?]', port)[0]
        
        if is_invalid_ip(host):
            return None

        # ВНОШЕСТВО: Парсим SNI для Vless Reality. Иногда основной host - обманка.
        query = parse_qs(parsed.query)
        sni = query.get('sni', [host])[0]

        # 1. Пингуем основной хост
        latency = check_socket(host, port)
        
        # 2. Если основной хост мертв, но есть домен SNI — пингуем его
        if latency is None and sni and sni != host and not is_invalid_ip(sni):
            latency = check_socket(sni, port)

        if latency is not None:
            return (latency, line)
    except:
        pass
    return None

def main():
    print("=== ЗАПУСК ПРОДВИНУТОГО ЧЕКЕРА (ВАРИАНТ 2) ===")
    checked_servers = []
    seen_configs = set()
    all_lines = []

    print("1. Скачиваем базы...")
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            text = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
            for line in text.splitlines():
                line = line.strip()
                # Берем только правильные протоколы
                if line and line.startswith(('vless://', 'vmess://', 'trojan://', 'ss://')):
                    if line not in seen_configs:
                        seen_configs.add(line)
                        all_lines.append(line)
        except Exception as e:
            print(f" Ошибка скачивания {url}: {e}")

    total_found = len(all_lines)
    print(f"Уникальных серверов собрано: {total_found}")

    # Увеличил пул проверок до 1000 для более жесткого отбора
    if total_found > 1000:
        random.shuffle(all_lines)
        all_lines = all_lines[:1000] 

    print(f"2. Запускаем жесткий пинг {len(all_lines)} серверов. Ждите...")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(process_line, line) for line in all_lines]
        for future in as_completed(futures):
            res = future.result()
            if res is not None:
                checked_servers.append(res)
                
    # 3. Сортируем по скорости (самые быстро-ответившие - в начало)
    checked_servers.sort(key=lambda x: x[0])
    
    # 4. СУПЕР ВАЖНО: Оставляем только ТОП-50 вместо 300.
    # Больше - не значит лучше. Лучше 50 живых, чем 300 полумертвых.
    top_servers = checked_servers[:50]
    working_servers = [line for latency, line in top_servers]

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    final_lines = [
        "# profile-title: 🌸ZLodeinVPN🌸",
        "# profile-update-interval: 1",
        f"# Последнее обновление: {timestamp} UTC",
        f"# Отобрано {len(working_servers)} железобетонных серверов"
    ]
    final_lines.extend(working_servers)

    with open("cleaned_sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))
    
    print("Готово! Файл сформирован.")

if __name__ == "__main__":
    main()
