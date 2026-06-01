import urllib.request
import time
import traceback
import random
from pathlib import Path
from python_v2ray.downloader import BinaryDownloader
from python_v2ray.tester import ConnectionTester
from python_v2ray.config_parser import parse_uri
import logging
from pprint import pprint

#отключение логов у библиотеки
logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)

#скачивает бинарники
project_root = Path("./")
try:
    downloader = BinaryDownloader(project_root)
    downloader.ensure_all()
except Exception as e:
    print(f"Fatal Error: {e}")

#источники
SOURCES = {
    "universal":"https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "nothing":"https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    "universal2":"https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "kal":"https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta7.txt",
    "kal2":"https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta6.txt",
    "nothing2":"https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "lte":"https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "lte2":"https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"
}

def test_all(parsed_configs):
    tester = ConnectionTester(
        vendor_path=str(project_root / "vendor"),
        core_engine_path=str(project_root / "core_engine")
    )
    results = tester.test_uris(parsed_configs, timeout=120)
    return results

def main():
    all_subs = {}
    #скачивание баз
    for url in SOURCES:
        try:
            all_subs[url] = []
            print(f"Скачиваю базу: {url}")
            req = urllib.request.Request(SOURCES[url], headers={'User-Agent': 'Mozilla/5.0'})
            text = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
            for line in text.splitlines():
                line = line.strip()
                if line and "://" in line and not line.startswith("#"):
                    if line not in all_subs[url]:
                        all_subs[url].append(line)
        except Exception as e:
            print(f"Ошибка при скачивании {url}: {e}")

    #проверка
    parse_all = []
    parse_dict_all = []
    for sub in all_subs:
        print(sub)
        parsed_dict = []
        urls = all_subs[sub]
        if len(urls) == 0: continue
        parsed = [p for p in (parse_uri(uri) for uri in urls) if p]
        for i in range(len(parsed)): parsed[i].tag=str(i)+"_"+sub
        for i in range(len(parsed)): parsed_dict.append(vars(parsed[i]).copy())
        for i in range(len(parsed_dict)): parsed_dict[i]["uri"] = urls[i]
        for i in range(len(parsed)): parsed[i].display_tag=str(i)+"_"+sub
        parse_all.extend(parsed)
        parse_dict_all.extend(parsed_dict)

    #сортировка по тегам
    tested = test_all(parse_all)
    servers_lookup = {server["tag"]: server for server in tested}
    for config in parse_dict_all:
        tag = config.get("tag")
        config["result"] = servers_lookup.get(tag)
    del parse_all

    parse_dict_all = [server for server in parse_dict_all if(server["result"]["ping_ms"]!=-1)]

    splited_subs = {}
    for sub in all_subs:
        splited_subs[sub] = []
    for sub in splited_subs:
        for config in parse_dict_all:
            if config["tag"].split("_")[1] == sub:
                splited_subs[sub].append(config)

    for sub in splited_subs:
        splited_subs[sub].sort(key=lambda x: x["result"]["ping_ms"])
        splited_subs[sub] = splited_subs[sub][:50]

    for sub in splited_subs:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        final_lines = [
            "# profile-title: 🌸ZlodeinVPN mod by ZloyGvozd🌸",
            "# profile-update-interval: 1",
            f"# Последнее обновление: {timestamp} UTC"
        ]
        out = []
        for server in splited_subs[sub]:
            out.append(server.get("uri"))
        final_lines.extend(out)

        with open(sub+".txt", "w", encoding="utf-8") as f:
            f.write("\n".join(final_lines))

if __name__ == "__main__":
    main()