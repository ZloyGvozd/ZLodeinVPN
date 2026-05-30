import urllib.request
import socket
import re
from urllib.parse import urlparse

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

def check_port(ip, port):
    try:
        socket.create_connection((ip, int(port)), timeout=2)
        return True
    except:
        return False

working_servers = []

for url in SOURCES:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        text = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        
        for line in text.splitlines():
            line = line.strip()
            # Пропускаем чужие строчки с названиями профилей
            if line.startswith("#") and "profile-" in line.lower():
                continue
            if not line.startswith("#") and "://" in line:
                if line not in working_servers:
                    clean = line.split('#')[0]
                    netloc = urlparse(clean).netloc.split("@")[-1]
                    if ":" in netloc:
                        host, port = netloc.split(":")[:2]
                        port = re.split(r'[/?]', port)[0]
                        
                        if check_port(host, port):
                            working_servers.append(line)
    except:
        pass

# Формируем файл СРАЗУ с твоим правильным названием профиля
final_lines = [
    "# profile-title: 🌸ZLodeinVPN🌸",       # Прописываем имя прямо в начало файла
    "# profile-update-interval: 1",    # Говорим приложению проверять обновление каждый час
    f"# Всего рабочих серверов: {len(working_servers)}"
]
final_lines.extend(working_servers)

# Сохраняем результат
with open("cleaned_sub.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(final_lines))
