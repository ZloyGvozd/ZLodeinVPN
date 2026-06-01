import urllib.request
import socket
import re
import time
import traceback
import random
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from python_v2ray.downloader import BinaryDownloader
from python_v2ray.tester import ConnectionTester
from python_v2ray.config_parser import parse_uri
import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)
import base64
from urllib.parse import quote, urlencode

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

#SOURCES = ["https://raw.githubusercontent.com/zlodeih/ZLodeinVPN/refs/heads/main/cleaned_sub.txt"]

project_root = Path("./")
print("--- Verifying binaries ---")
try:
    downloader = BinaryDownloader(project_root)
    downloader.ensure_all()
except Exception as e:
    print(f"Fatal Error: {e}")

def test_all(parsed_configs):
    #print(f"Parsed configs: {parsed_configs}")
    tester = ConnectionTester(
        vendor_path=str(project_root / "vendor"),
        core_engine_path=str(project_root / "core_engine")
    )
    results = tester.test_uris(parsed_configs, timeout=60)
    #print(f"Results: {results}")
    return results

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

    print(f"Запускаю проверки {len(all_lines)} конфигураций...")

    reserve_tags = {}
    parsed_configs = [p for p in (parse_uri(uri) for uri in all_lines) if p]
    for i in range(len(parsed_configs)):
        reserve_tags[i] = parsed_configs[i].display_tag
        parsed_configs[i].tag = str(i)
        parsed_configs[i].display_tag = str(i)

    print(parsed_configs[0])
    checked_servers = test_all(parsed_configs)

    parsed_configs = [vars(obj) for obj in parsed_configs]

    # 1. Создаем быстрый справочник из второго списка по ключу "tag"
    servers_lookup = {server["tag"]: server for server in checked_servers}

    # 2. Проходим по первому списку и безопасно добавляем совпадения
    for config in parsed_configs:
        tag = config.get("tag")
        # Ищем сервер по тегу. Если не нашли, запишется None (можно заменить на {})
        config["result"] = servers_lookup.get(tag)

    for config in parsed_configs:
        config["uri"] = all_lines[int(config.get("tag"))]

    for config in parsed_configs:
        config["tag"] = reserve_tags[int(config.get("tag"))]

    print(f"Проверка завершена! Найдено живых серверов: {len(checked_servers)}")

    #print(parsed_configs)
    parsed_configs = [server for server in parsed_configs if(server["result"]["ping_ms"]!=-1)]
    parsed_configs.sort(key=lambda x: x["result"]["ping_ms"])
    top_fast_servers = parsed_configs[:200]
    print(top_fast_servers)

    out = []
    for server in top_fast_servers:
        out.append(server.get("uri"))
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # 4. Формируем файл
    final_lines = [
        "# profile-title: 🌸ZlodeinVPN mod by ZloyGvozd🌸",
        "# profile-update-interval: 1",
        f"# Последнее обновление: {timestamp} UTC",
        f"# Всего проверено: {len(all_lines)} | Живых: {len(checked_servers)} | Отобрано топ лучших"
    ]
    final_lines.extend(out)

    with open("cleaned_sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))

    print(f" Результат успешно сохранен в cleaned_sub.txt!")


if __name__ == "__main__":
    try:
        main()
        None
    except Exception as e:
        print("!!! КРИТИЧЕСКИЙ СБОЙ СКРИПТА !!!")
        traceback.print_exc()
        exit(1)

#process_line("vless://77777777-8a3e-6666-b6d1-a9c5f0e8b3a2@172.64.52.24:2087?security=tls&sni=fgnix832fx.fx6hsv0.ccwu.cc&type=ws&headerType=none&host=fgnix832fx.fx6hsv0.ccwu.cc&path=/#%F0%9F%87%A9%F0%9F%87%AA%20%5BVL%5D%20%D0%93%D0%B5%D1%80%D0%BC%D0%B0%D0%BD%D0%B8%D1%8F%20%237650%20%7C%20%D0%A0%D0%BE%D1%81%D0%A2%D1%83%D0%BD%D0%BD%D0%B5%D0%BB%D1%8C%20t.me%2Frjsxrd")