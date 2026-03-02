import socket
import threading
import time
import sys
import requests
import whois
import tkinter as tk
from tkinter import scrolledtext, messagebox, END, Entry, Label, Button
from tkinter import ttk
from datetime import datetime
import os
import webbrowser
import ssl
import json
import subprocess

try:
    import folium
except ImportError:
    folium = None

# ═══════════════════════════════════════════
# CONFIG & AUTO-UPDATE
# ═══════════════════════════════════════════
APP_VERSION    = "5.1"
VERSION_URL    = "https://raw.githubusercontent.com/your-username/flash-tool/main/version.txt"
UPDATE_URL     = "https://raw.githubusercontent.com/your-username/flash-tool/main/flash.py"
USER_DATA_FILE = os.path.join(os.path.expanduser("~"), ".flash_user.json")

def load_user_data():
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {}

def save_user_data(data):
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass

def check_for_update():
    try:
        resp = requests.get(VERSION_URL, timeout=5)
        if resp.status_code == 200:
            latest = resp.text.strip()
            if latest != APP_VERSION:
                return latest
    except: pass
    return None

# ═══════════════════════════════════════════
# SPLASH SCREEN
# ═══════════════════════════════════════════
def show_splash_and_name():
    user_data = load_user_data()
    username  = user_data.get("username", "")

    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#0A0A0A")
    w, h = 700, 500
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    canvas = tk.Canvas(splash, width=w, height=h, bg="#0A0A0A", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Grid background
    for i in range(0, w, 40):
        canvas.create_line(i, 0, i, h, fill="#0D1117", width=1)
    for i in range(0, h, 40):
        canvas.create_line(0, i, w, i, fill="#0D1117", width=1)

    # Border
    canvas.create_rectangle(2, 2, w-2, h-2, outline="#2563EB", width=2)
    canvas.create_rectangle(6, 6, w-6, h-6, outline="#1E3A8A", width=1)

    # Logo & title
    canvas.create_text(w//2, 80,  text="⚡",             font=("Segoe UI", 60),      fill="#2563EB")
    canvas.create_text(w//2, 160, text="FLASH",           font=("Consolas", 48, "bold"), fill="white")
    canvas.create_text(w//2, 210, text="Control Center",  font=("Consolas", 14),      fill="#475569")
    canvas.create_text(w//2, 235, text=f"v{APP_VERSION}", font=("Consolas", 10),      fill="#2563EB")
    canvas.create_line(100, 260, w-100, 260, fill="#1E3A8A", width=1)

    status_lbl = canvas.create_text(w//2, 290, text="", font=("Consolas", 11), fill="#94A3B8")
    canvas.create_rectangle(100, 430, w-100, 448, fill="#1E293B", outline="#334155")
    bar_fg  = canvas.create_rectangle(100, 430, 100, 448, fill="#2563EB", outline="")
    bar_pct = canvas.create_text(w//2, 439, text="0%", font=("Consolas", 9), fill="white")

    name_saved = [username]
    widgets_to_destroy = []

    def update_bar(pct, text=""):
        bar_w = int((w - 200) * pct / 100)
        canvas.coords(bar_fg, 100, 430, 100 + bar_w, 448)
        canvas.itemconfig(bar_pct, text=f"{pct}%")
        if text:
            canvas.itemconfig(status_lbl, text=text, fill="#94A3B8")
        splash.update()

    def show_name_input():
        canvas.create_text(w//2, 285, text="مرحباً! أدخل اسمك للمتابعة 👋",
                           font=("Consolas", 13, "bold"), fill="#2563EB", tags="nameui")

        nf = tk.Frame(splash, bg="#1E293B", highlightthickness=2, highlightbackground="#2563EB")
        nf.place(x=150, y=315, width=400, height=45)
        tk.Label(nf, text="👤", font=("Segoe UI", 14), bg="#1E293B", fg="#2563EB").pack(side=tk.LEFT, padx=10)
        ne = tk.Entry(nf, font=("Consolas", 14), bg="#1E293B", fg="white",
                      insertbackground="#2563EB", bd=0, relief="flat")
        ne.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ne.focus()

        btn = tk.Button(splash, text="▶  دخول", font=("Consolas", 12, "bold"),
                        bg="#2563EB", fg="white", activebackground="#1D4ED8",
                        bd=0, padx=20, pady=8, cursor="hand2")
        btn.place(x=270, y=373, width=160, height=38)
        widgets_to_destroy.extend([nf, btn])

        def confirm():
            name = ne.get().strip()
            if not name:
                canvas.itemconfig(status_lbl, text="⚠️ أدخل اسمك أولاً!", fill="#EF4444")
                return
            name_saved[0] = name
            d = load_user_data()
            d["username"] = name
            d["first_run"] = str(datetime.now())
            save_user_data(d)
            for wg in widgets_to_destroy:
                try: wg.destroy()
                except: pass
            canvas.delete("nameui")
            threading.Thread(target=start_loading, daemon=True).start()

        btn.config(command=confirm)
        ne.bind("<Return>", lambda e: confirm())

    def start_loading():
        uname = name_saved[0]
        steps = [
            (5,  f"مرحباً {uname}! 👋  جارٍ التهيئة..."),
            (15, "⚡ تحميل النواة الرئيسية..."),
            (25, "🔧 تهيئة وحدات الفحص..."),
            (35, "🌐 الاتصال بالخوادم..."),
            (45, "🛡️ تحميل قاعدة الأمان..."),
            (55, "📡 تهيئة وحدة DNS..."),
            (65, "🔍 تحميل محرك OSINT..."),
            (72, "🔎 فحص التحديثات..."),
        ]
        for pct, msg in steps:
            update_bar(pct, msg)
            time.sleep(0.28)

        # ── Auto-install missing libraries ──
        required_libs = [
            ("requests",      "requests"),
            ("whois",         "python-whois"),
            ("folium",        "folium"),
            ("phonenumbers",  "phonenumbers"),
        ]
        for import_name, pip_name in required_libs:
            try:
                __import__(import_name)
            except ImportError:
                update_bar(70, f"📦 تثبيت {pip_name}...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pip_name, "-q"],
                        timeout=60,
                        capture_output=True
                    )
                    update_bar(70, f"✅ تم تثبيت {pip_name}!")
                    time.sleep(0.3)
                except Exception:
                    update_bar(70, f"⚠️ تعذر تثبيت {pip_name}")
                    time.sleep(0.3)

        # Auto-update check
        latest = check_for_update()
        if latest:
            update_bar(75, f"🆕 تحديث v{latest} متاح! جارٍ التحميل...")
            time.sleep(0.4)
            try:
                resp = requests.get(UPDATE_URL, timeout=15)
                if resp.status_code == 200:
                    script_path = os.path.abspath(sys.argv[0])
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(resp.text)
                    update_bar(85, "✅ تم التحديث! إعادة التشغيل...")
                    time.sleep(1)
            except:
                update_bar(75, "⚠️ تعذر التحديث، استمرار...")
        else:
            update_bar(75, "✅ النسخة محدثة!")
            time.sleep(0.2)

        final_steps = [
            (82, "🎨 تحميل الواجهة..."),
            (90, "📊 تهيئة لوحة التحكم..."),
            (96, "🔐 تفعيل بروتوكولات الأمان..."),
            (100, f"✅ جاهز! أهلاً {uname} ⚡"),
        ]
        for pct, msg in final_steps:
            update_bar(pct, msg)
            time.sleep(0.3)

        time.sleep(0.6)
        splash.destroy()

    if username:
        canvas.create_text(w//2, 285, text=f"أهلاً بعودتك {username}! ⚡",
                           font=("Consolas", 14, "bold"), fill="#2563EB")
        splash.after(400, lambda: threading.Thread(target=start_loading, daemon=True).start())
    else:
        splash.after(300, show_name_input)

    splash.mainloop()
    return load_user_data()

# ── Launch splash ──
USER_DATA    = show_splash_and_name()
CURRENT_USER = USER_DATA.get("username", "مجهول")


# --- إعدادات المسح ---
COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 3389, 5900, 8080]
GEOIP_API_URL = "https://ipinfo.io/{}/json"
HACKERTARGET_API_URL = "https://api.hackertarget.com/{}/?q={}"

last_geoip_coords = None

# ═══════════════════════════════════════════
# COLORS & THEME
# ═══════════════════════════════════════════
BG_MAIN       = "#F5F6FA"
BG_CARD       = "#FFFFFF"
BG_SIDEBAR    = "#1A1A2E"
ACCENT_BLUE   = "#2563EB"
ACCENT_RED    = "#DC2626"
ACCENT_GREEN  = "#16A34A"
ACCENT_ORANGE = "#EA580C"
TEXT_DARK     = "#0F172A"
TEXT_MID      = "#475569"
TEXT_LIGHT    = "#94A3B8"
BORDER        = "#E2E8F0"
CONSOLE_BG    = "#0F172A"
CONSOLE_FG    = "#E2E8F0"

# ═══════════════════════════════════════════
# HELPER: CONSOLE OUTPUT
# ═══════════════════════════════════════════
def update_console_status(message, is_error=False, style_tag="normal"):
    console_text.config(state=tk.NORMAL)
    tag = "error" if is_error else style_tag
    timestamp = datetime.now().strftime("%H:%M:%S")
    console_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
    console_text.see(tk.END)
    console_text.config(state=tk.DISABLED)

def clear_console():
    console_text.config(state=tk.NORMAL)
    console_text.delete(1.0, tk.END)
    console_text.config(state=tk.DISABLED)
    update_console_status("تم مسح الكونسول.", style_tag="info")

# ═══════════════════════════════════════════
# MAP
# ═══════════════════════════════════════════
def open_map_location_gui():
    global last_geoip_coords
    if not last_geoip_coords or not folium:
        messagebox.showerror("خطأ في الخريطة", "لا توجد إحداثيات متاحة أو Folium غير مثبت.")
        return
    try:
        lat, lon = map(float, last_geoip_coords.split(','))
        m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
        folium.Marker([lat, lon], popup=f"الهدف: {recon_target_entry.get()}",
                      icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
        map_filename = "target_location.html"
        m.save(map_filename)
        webbrowser.open_new_tab(map_filename)
        update_console_status(f"🌍 تم فتح الخريطة للهدف {recon_target_entry.get()} في المتصفح.", style_tag="success")
    except Exception as e:
        update_console_status(f"خطأ في فتح الخريطة: {e}", is_error=True)

# ═══════════════════════════════════════════
# API & RECON FUNCTIONS
# ═══════════════════════════════════════════
def get_external_api_info(api_type, target):
    try:
        url = HACKERTARGET_API_URL.format(api_type, target)
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            if "error check your api usage" in response.text.lower():
                return f"تجاوز حد الاستخدام المجاني لـ {api_type}. انتظر أو استخدم بروكسي.", True
            return response.text.strip(), False
        else:
            return f"HackerTarget API Error ({api_type}): HTTP {response.status_code}", True
    except Exception as e:
        return f"خطأ في API ({api_type}): {e}", True

def get_geoip_info(target_ip):
    global last_geoip_coords
    try:
        response = requests.get(GEOIP_API_URL.format(target_ip), timeout=10)
        data = response.json()
        if response.status_code != 200 or data.get('error'):
            last_geoip_coords = None
            return f"خطأ في GeoIP API: {data.get('error', {}).get('message', 'Unknown')}"
        if data.get('bogon'):
            last_geoip_coords = None
            return "الـ IP داخلي/محجوز (bogon). لا ينطبق تحديد الموقع."
        info = [f"🌍 الموقع الجغرافي للـ {target_ip}:"]
        if data.get('city'):     info.append(f"   📍 المدينة     : {data['city']}")
        if data.get('region'):   info.append(f"   🗺️  المنطقة     : {data['region']}")
        if data.get('country_name'): info.append(f"   🌐 البلد       : {data['country_name']} ({data.get('country')})")
        if data.get('loc'):
            info.append(f"   📌 الإحداثيات : {data['loc']}")
            last_geoip_coords = data['loc']
        else:
            last_geoip_coords = None
        if data.get('org'):      info.append(f"   🏢 المنظمة     : {data['org']}")
        if data.get('hostname'): info.append(f"   💻 المضيف      : {data['hostname']}")
        if data.get('postal'):   info.append(f"   📮 البريدي     : {data['postal']}")
        if data.get('timezone'): info.append(f"   🕐 التوقيت     : {data['timezone']}")
        return "\n".join(info)
    except Exception as e:
        last_geoip_coords = None
        return f"خطأ أثناء بحث GeoIP: {e}"

def get_service_banner(ip, port, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        if port == 80:
            sock.sendall(b"GET / HTTP/1.0\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0\r\n\r\n")
        elif port == 443:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sslsock = context.wrap_socket(sock, server_hostname=ip)
            sslsock.sendall(b"GET / HTTP/1.0\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0\r\n\r\n")
            sock = sslsock
        elif port == 21:
            sock.sendall(b"HELP\r\n")
        elif port == 25:
            sock.sendall(b"HELO attacker.com\r\n")
        banner = sock.recv(2048).decode('utf-8', errors='ignore').strip()
        sock.close()
        return banner.split('\n')[0] if banner else "لا توجد لافتة."
    except Exception:
        return "لا توجد لافتة."

def scan_ports_recon(target_ip, ports_to_scan):
    output = [f"⚡ مسح المنافذ للـ {target_ip}..."]
    open_ports_found = False
    try:
        resolved_ip = socket.gethostbyname(target_ip)
        output.append(f"   ✅ الـ IP المحوَّل : {resolved_ip}")
    except socket.gaierror:
        output.append("   ❌ تعذر حل اسم المضيف.")
        return "\n".join(output)
    for port in ports_to_scan:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((resolved_ip, port))
            if result == 0:
                open_ports_found = True
                banner = get_service_banner(resolved_ip, port)
                output.append(f"   🔓 المنفذ {port:5d} مفتوح  ←  {banner}")
            sock.close()
        except Exception:
            pass
    if not open_ports_found:
        output.append("   🔒 لم يتم العثور على منافذ مفتوحة.")
    output.append("⚡ اكتمل مسح المنافذ.")
    return "\n".join(output)

def get_whois_info_recon(target):
    try:
        domain_info = whois.whois(target)
        output = [f"📜 معلومات WHOIS للـ {target}:"]
        if domain_info and any(domain_info.values()):
            priority_keys = ['registrar', 'name_servers', 'status', 'creation_date', 'expiration_date', 'emails', 'org', 'address']
            for key in priority_keys:
                value = domain_info.get(key)
                if value:
                    if isinstance(value, list):
                        output.append(f"   {key.replace('_',' ').title()}:")
                        for item in value[:5]:
                            output.append(f"     • {item}")
                    else:
                        output.append(f"   {key.replace('_',' ').title()}: {value}")
        else:
            output.append("   لم يتم العثور على سجل WHOIS.")
        return "\n".join(output)
    except Exception as e:
        return f"خطأ أثناء بحث WHOIS: {e}"

def get_reverse_dns_recon(target_ip):
    try:
        resolved_ip = socket.gethostbyname(target_ip)
        hostname, aliases, ips = socket.gethostbyaddr(resolved_ip)
        output = [f"🔍 DNS العكسي للـ {resolved_ip}:"]
        output.append(f"   اسم المضيف : {hostname}")
        if aliases: output.append(f"   الأسماء المستعارة: {', '.join(aliases)}")
        if ips:     output.append(f"   IPs المرتبطة    : {', '.join(ips)}")
        return "\n".join(output)
    except Exception as e:
        return f"خطأ في DNS العكسي: {e}"

def get_http_headers_recon(target):
    output = [f"🌐 رؤوس HTTP/HTTPS للـ {target}:"]
    for scheme in ["https://", "http://"]:
        try:
            response = requests.head(scheme + target, timeout=10, allow_redirects=True)
            output.append(f"   ─── {scheme}{target} (HTTP {response.status_code}) ───")
            for header, value in response.headers.items():
                output.append(f"   {header}: {value}")
            return "\n".join(output)
        except requests.exceptions.ConnectionError:
            continue
        except Exception as e:
            output.append(f"   خطأ: {e}")
            break
    return "\n".join(output) + "\n   فشل الاتصال."

def analyze_http_security_headers_recon(target):
    output = [f"🔒 رؤوس الأمان لـ {target}:"]
    try:
        response = requests.get(f"https://{target}", timeout=10, allow_redirects=True)
        security_headers = {
            "Strict-Transport-Security": "HSTS",
            "Content-Security-Policy": "CSP",
            "X-Frame-Options": "X-Frame-Options",
            "X-Content-Type-Options": "X-Content-Type-Options",
            "Referrer-Policy": "Referrer-Policy",
            "Permissions-Policy": "Permissions-Policy",
        }
        for header, label in security_headers.items():
            if header in response.headers:
                output.append(f"   ✅ {label}: {response.headers[header][:80]}")
            else:
                output.append(f"   ❌ {label}: مفقود")
    except Exception as e:
        output.append(f"   خطأ: {e}")
    return "\n".join(output)

def detect_waf_cdn_recon(target):
    output = [f"🛡️ كشف WAF/CDN للـ {target}:"]
    try:
        dns_info_raw, _ = get_external_api_info("dnslookup", target)
        if "cloudflare.com" in dns_info_raw: output.append("   ✅ Cloudflare (من DNS)")
        if "akamai.net"     in dns_info_raw: output.append("   ✅ Akamai (من DNS)")
        try:
            response = requests.head(f"http://{target}", timeout=5, allow_redirects=True)
            sh = response.headers.get('Server', '').lower()
            if 'cloudflare' in sh: output.append("   ✅ Cloudflare (من Server header)")
            if 'sucuri'     in sh: output.append("   ✅ Sucuri WAF (من Server header)")
            if 'incapsula'  in response.headers.get('Set-Cookie', '').lower():
                output.append("   ✅ Incapsula WAF (من Cookie)")
        except: pass
        if len(output) == 1: output.append("   ❌ لم يتم الكشف عن WAF/CDN معروف.")
    except Exception as e:
        output.append(f"   خطأ: {e}")
    return "\n".join(output)

def get_ssl_cert_info_recon(target_host, port=443):
    output = [f"🔒 شهادة SSL/TLS لـ {target_host}:{port}:"]
    try:
        context = ssl.create_default_context()
        with socket.create_connection((target_host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=target_host) as sslsock:
                cert = sslsock.getpeercert()
                output.append(f"   جهة الإصدار : {dict(x[0] for x in cert['issuer']).get('commonName','N/A')}")
                output.append(f"   صالح من     : {cert['notBefore']}")
                output.append(f"   صالح حتى    : {cert['notAfter']}")
                output.append(f"   الاسم       : {dict(x[0] for x in cert['subject']).get('commonName','N/A')}")
                if 'subjectAltName' in cert:
                    alt_names = [n[1] for n in cert['subjectAltName']]
                    output.append(f"   SAN         : {', '.join(alt_names[:5])}")
                output.append(f"   البروتوكول  : {sslsock.version()}")
    except Exception as e:
        output.append(f"   خطأ: {e}")
    return "\n".join(output)

def get_dnssec_status_recon(target_domain):
    output = [f"🛡️ حالة DNSSEC لـ {target_domain}:"]
    try:
        dns_info_raw, is_err = get_external_api_info("dnslookup", target_domain)
        if not is_err and "RRSIG" in dns_info_raw and "DNSKEY" in dns_info_raw:
            output.append("   ✅ DNSSEC ممكَّن (RRSIG + DNSKEY موجودان)")
        elif not is_err:
            output.append("   ❌ DNSSEC غير ممكَّن")
        else:
            output.append(f"   خطأ: {dns_info_raw}")
    except Exception as e:
        output.append(f"   خطأ: {e}")
    return "\n".join(output)

def run_traceroute_recon(target_host):
    output = [f"🛣️ Traceroute إلى {target_host}:"]
    try:
        if sys.platform.startswith('win'):
            command = ["tracert", "-d", "-h", "30", target_host]
        else:
            command = ["traceroute", "-n", "-m", "30", target_host]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=45)
        if stdout: output.append(stdout.strip())
        if stderr: output.append(f"خطأ: {stderr.strip()}")
    except subprocess.TimeoutExpired:
        process.kill()
        output.append("انتهت مهلة Traceroute.")
    except Exception as e:
        output.append(f"خطأ: {e}")
    return "\n".join(output)

# ═══════════════════════════════════════════
# MAIN RECON ORCHESTRATOR
# ═══════════════════════════════════════════
def perform_full_recon_gui():
    target_input = recon_target_entry.get().strip()
    if not target_input:
        messagebox.showerror("خطأ", "أدخل عنوان IP أو نطاق الهدف.")
        return
    recon_button.config(state=tk.DISABLED, text="⏳ جارٍ الفحص...")
    status_label.config(text=f"● فحص: {target_input}", fg=ACCENT_ORANGE)
    update_console_status(f"\n{'═'*60}", style_tag="separator")
    update_console_status(f"  🚀 بدء الفحص الشامل للهدف: {target_input}", style_tag="header")
    update_console_status(f"{'═'*60}\n", style_tag="separator")
    threading.Thread(target=_run_full_recon, args=(target_input,), daemon=True).start()

def _run_full_recon(target_input):
    global last_geoip_coords
    last_geoip_coords = None

    steps = [
        ("🌍 الموقع الجغرافي (GeoIP)",          lambda: get_geoip_info(target_input)),
        ("🛣️ Traceroute",                         lambda: run_traceroute_recon(target_input)),
        ("🔍 DNS العكسي",                         lambda: get_reverse_dns_recon(target_input)),
        ("📡 سجلات DNS الكاملة",                  lambda: get_external_api_info("dnslookup", target_input)),
        ("🔗 النطاقات الفرعية",                   lambda: get_external_api_info("hostsearch", target_input)),
        ("📧 البريد الإلكتروني المرتبط",           lambda: get_external_api_info("emaillookup", target_input)),
        ("🛡️ كشف WAF/CDN",                        lambda: detect_waf_cdn_recon(target_input)),
        ("🌐 رؤوس HTTP/HTTPS",                    lambda: get_http_headers_recon(target_input)),
        ("🔒 رؤوس الأمان",                        lambda: analyze_http_security_headers_recon(target_input)),
        ("🔐 شهادة SSL/TLS",                      lambda: get_ssl_cert_info_recon(target_input)),
        ("🛡️ حالة DNSSEC",                        lambda: get_dnssec_status_recon(target_input)),
        ("⚡ مسح المنافذ",                         lambda: scan_ports_recon(target_input, COMMON_PORTS)),
        ("📜 WHOIS",                               lambda: get_whois_info_recon(target_input)),
    ]

    total = len(steps)
    for i, (label, func) in enumerate(steps, 1):
        update_console_status(f"\n[{i}/{total}] {label}...", style_tag="section")
        try:
            result = func()
            if isinstance(result, tuple):
                text, is_err = result
                update_console_status(text, is_error=is_err)
            else:
                update_console_status(result)
        except Exception as e:
            update_console_status(f"خطأ: {e}", is_error=True)
        
        progress = int((i / total) * 100)
        progress_bar['value'] = progress
        progress_label.config(text=f"{progress}%")

    # Update map button
    if last_geoip_coords and folium:
        open_map_button.config(state=tk.NORMAL)
    
    update_console_status(f"\n{'═'*60}", style_tag="separator")
    update_console_status(f"  ✅ اكتمل الفحص الشامل للهدف: {target_input}", style_tag="success")
    update_console_status(f"{'═'*60}\n", style_tag="separator")

    recon_button.config(state=tk.NORMAL, text="🚀 فحص شامل")
    status_label.config(text=f"✅ اكتمل: {target_input}", fg=ACCENT_GREEN)
    progress_bar['value'] = 100

# ═══════════════════════════════════════════
# DISCORD LOOKUP
# ═══════════════════════════════════════════
def fetch_discord_info(user_id):
    """Fetch Discord user info via public API (no token needed for basic info)."""
    try:
        # Discord public widget / invite lookup won't work without token
        # But we can use the public user endpoint with a bot token
        # Without token: only limited info via invite or widget
        # Best free method: lanyard API (shows online status if user uses it)
        # and discord.id / discordlookup.com style

        result = {"id": user_id}

        # ── Method 1: Lanyard API (free, no token) ──
        try:
            lanyard_url = f"https://api.lanyard.rest/v1/users/{user_id}"
            resp = requests.get(lanyard_url, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                discord = data.get("discord_user", {})
                if discord:
                    result["username"]      = discord.get("username", "")
                    result["display_name"]  = discord.get("display_name") or discord.get("global_name", "")
                    result["discriminator"] = discord.get("discriminator", "0")
                    result["avatar"]        = discord.get("avatar", "")
                    result["public_flags"]  = discord.get("public_flags", 0)
                    result["bot"]           = discord.get("bot", False)

                    # Status
                    status_map = {
                        "online":  "🟢 متصل (Online)",
                        "idle":    "🌙 غائب (Idle)",
                        "dnd":     "🔴 لا تزعج (DND)",
                        "offline": "⚫ غير متصل (Offline)",
                    }
                    result["status"] = status_map.get(data.get("discord_status", "offline"), "⚫ غير متصل")

                    # Activities / Bio
                    activities = data.get("activities", [])
                    for act in activities:
                        if act.get("type") == 4:  # Custom status
                            result["custom_status"] = act.get("state", "")
                            emoji = act.get("emoji", {})
                            if emoji:
                                result["status_emoji"] = emoji.get("name", "")

                    result["source"] = "Lanyard API"
                    return result
        except Exception:
            pass

        # ── Method 2: Discord lookup via public profile endpoint ──
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            url2 = f"https://discordlookup.mesalytic.com/v1/user/{user_id}"
            resp2 = requests.get(url2, headers=headers, timeout=8)
            if resp2.status_code == 200:
                d = resp2.json()
                result["username"]     = d.get("username", "")
                result["display_name"] = d.get("global_name") or d.get("username", "")
                result["discriminator"]= d.get("legacy_username", "")
                result["avatar"]       = d.get("avatar", {}).get("link", "")
                result["public_flags"] = d.get("public_flags", {})
                result["created_at"]   = d.get("created_at", "")
                result["source"]       = "DiscordLookup API"
                return result
        except Exception:
            pass

        # ── Method 3: discord.id API ──
        try:
            url3 = f"https://discord.id/api/user/{user_id}"
            resp3 = requests.get(url3, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            if resp3.status_code == 200:
                d = resp3.json()
                result["username"]     = d.get("tag", d.get("username", ""))
                result["display_name"] = d.get("username", "")
                result["avatar"]       = d.get("avatar_url", "")
                result["created_at"]   = d.get("created_at", "")
                result["source"]       = "discord.id"
                return result
        except Exception:
            pass

        return {"exists": None, "error": "تعذر جلب المعلومات. تأكد من صحة الـ ID أو أن المستخدم عام."}

    except Exception as e:
        return {"exists": None, "error": str(e)}


def get_discord_badges(flags):
    """Convert Discord flags to badge names."""
    badges = []
    if isinstance(flags, int):
        flag_map = {
            1 << 0:  "👑 Discord Staff",
            1 << 1:  "🤝 Partner",
            1 << 2:  "🎉 HypeSquad Events",
            1 << 3:  "🐛 Bug Hunter",
            1 << 6:  "🏠 HypeSquad Bravery",
            1 << 7:  "🏠 HypeSquad Brilliance",
            1 << 8:  "🏠 HypeSquad Balance",
            1 << 9:  "🌟 Early Supporter",
            1 << 14: "🐛 Bug Hunter Gold",
            1 << 17: "🤖 Bot HTTP Interactions",
            1 << 18: "✅ Verified Bot",
            1 << 19: "👨‍💻 Early Verified Bot Dev",
            1 << 22: "🎭 Active Developer",
        }
        for flag, name in flag_map.items():
            if flags & flag:
                badges.append(name)
    elif isinstance(flags, dict):
        for key, val in flags.items():
            if val:
                badges.append(f"✅ {key.replace('_', ' ').title()}")
    return badges


# ═══════════════════════════════════════════
# PHONE NUMBER LOOKUP
# ═══════════════════════════════════════════
def fetch_phone_info(number):
    """Fetch phone number info using multiple free APIs."""
    result = {"number": number}

    # Clean number
    clean = number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not clean.startswith("+"):
        clean = "+" + clean
    result["formatted"] = clean

    # ── Method 1: numverify (free tier) ──
    try:
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={clean}"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("valid") is not None:
                result["valid"]    = d.get("valid", False)
                result["country"]  = d.get("country", {}).get("name", "")
                result["location"] = d.get("location", "")
                result["carrier"]  = d.get("carrier", "")
                result["type"]     = d.get("type", "")
                result["source"]   = "AbstractAPI"
                return result
    except: pass

    # ── Method 2: phone-number API ──
    try:
        url2 = f"https://api.apilayer.com/number_verification/validate?number={clean}"
        resp2 = requests.get(url2, timeout=8, headers={"apikey": "free"})
        if resp2.status_code == 200:
            d = resp2.json()
            result["valid"]       = d.get("valid", False)
            result["country"]     = d.get("country_name", "")
            result["location"]    = d.get("location", "")
            result["carrier"]     = d.get("carrier", "")
            result["type"]        = d.get("line_type", "")
            result["country_code"]= d.get("country_code", "")
            result["timezone"]    = d.get("timezones", [""])[0] if d.get("timezones") else ""
            result["source"]      = "APILayer"
            return result
    except: pass

    # ── Method 3: phonenumbers library (offline) ──
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone as pntimezone

        parsed = phonenumbers.parse(clean, None)
        result["valid"]        = phonenumbers.is_valid_number(parsed)
        result["possible"]     = phonenumbers.is_possible_number(parsed)
        result["country"]      = geocoder.description_for_number(parsed, "ar") or geocoder.description_for_number(parsed, "en")
        result["carrier"]      = carrier.name_for_number(parsed, "en")
        result["timezone"]     = ", ".join(pntimezone.time_zones_for_number(parsed))
        result["country_code"] = f"+{parsed.country_code}"
        result["national"]     = str(parsed.national_number)

        # Number type
        num_type = phonenumbers.number_type(parsed)
        type_map = {
            0: "📱 موبايل",
            1: "☎️ أرضي",
            2: "📠 فاكس أرضي",
            3: "📠 فاكس موبايل",
            4: "📟 بيجر",
            5: "🌐 VoIP",
            6: "📞 Personal",
            7: "📺 Premium Rate",
            8: "💰 Shared Cost",
            9: "🆓 Toll Free",
            10: "🌍 Universal",
        }
        result["type"]   = type_map.get(num_type, "غير معروف")
        result["source"] = "phonenumbers (offline)"
        return result
    except ImportError:
        result["_no_lib"] = True
    except Exception as e:
        result["error"] = str(e)

    return result


def open_phone_window():
    """Open Phone Number Lookup window."""
    ph_win = tk.Toplevel(root)
    ph_win.title("📞 Phone Number Lookup")
    ph_win.geometry("620x650")
    ph_win.configure(bg="#0A1A0A")
    ph_win.resizable(False, False)

    # ── Header ──
    header = tk.Frame(ph_win, bg="#0D2B0D", height=75)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(header, text="📞  Phone Number Lookup",
             font=("Segoe UI", 16, "bold"), bg="#0D2B0D", fg="white").pack(pady=8)
    tk.Label(header, text="فحص أي رقم هاتف في العالم • بيانات عامة فقط",
             font=("Consolas", 8), bg="#0D2B0D", fg="#4ADE80").pack()

    # ── Input ──
    input_frame = tk.Frame(ph_win, bg="#0D2B0D", pady=15)
    input_frame.pack(fill=tk.X, padx=20, pady=10)

    tk.Label(input_frame, text="رقم الهاتف (مع مفتاح الدولة):",
             font=("Consolas", 10, "bold"), bg="#0D2B0D", fg="#4ADE80").pack(anchor="w", padx=10)

    entry_frame = tk.Frame(input_frame, bg="#1A3A1A",
                           highlightthickness=2,
                           highlightbackground="#16A34A",
                           highlightcolor="#4ADE80")
    entry_frame.pack(fill=tk.X, padx=10, pady=5)

    tk.Label(entry_frame, text="📞", font=("Segoe UI", 13),
             bg="#1A3A1A", fg="#16A34A").pack(side=tk.LEFT, padx=(10, 0))

    ph_entry = tk.Entry(entry_frame, font=("Consolas", 13),
                        bg="#1A3A1A", fg="white",
                        insertbackground="#16A34A",
                        bd=0, relief="flat")
    ph_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=8)
    ph_entry.insert(0, "+966501234567")
    ph_entry.config(fg="#4ADE80")

    def on_click(e):
        if ph_entry.get() == "+966501234567":
            ph_entry.delete(0, tk.END)
            ph_entry.config(fg="white")
    ph_entry.bind("<FocusIn>", on_click)

    tk.Label(input_frame,
             text="💡 مثال: +966501234567 (السعودية) | +213550123456 (الجزائر) | +2126XXXXXXXX (المغرب)",
             font=("Consolas", 8), bg="#0D2B0D", fg="#16A34A",
             wraplength=560, justify="right").pack(padx=10, pady=(2, 5))

    # ── Result ──
    result_frame = tk.Frame(ph_win, bg="#0A1A0A")
    result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD,
                                             bg="#0D2B0D", fg="#DCFCE7",
                                             font=("Consolas", 10),
                                             bd=0, relief="flat",
                                             padx=15, pady=10,
                                             state=tk.DISABLED)
    result_text.pack(fill=tk.BOTH, expand=True)
    result_text.tag_config("title",   foreground="#4ADE80", font=("Consolas", 13, "bold"))
    result_text.tag_config("key",     foreground="#16A34A", font=("Consolas", 10, "bold"))
    result_text.tag_config("value",   foreground="#DCFCE7")
    result_text.tag_config("valid",   foreground="#22C55E", font=("Consolas", 11, "bold"))
    result_text.tag_config("invalid", foreground="#EF4444", font=("Consolas", 11, "bold"))
    result_text.tag_config("warning", foreground="#FAA61A")
    result_text.tag_config("divider", foreground="#1A3A1A")
    result_text.tag_config("info",    foreground="#4ADE80")

    def insert_r(text, tag="value"):
        result_text.config(state=tk.NORMAL)
        result_text.insert(tk.END, text, tag)
        result_text.config(state=tk.DISABLED)

    def clear_r():
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.config(state=tk.DISABLED)

    def do_lookup():
        number = ph_entry.get().strip()
        if not number or number == "+966501234567":
            messagebox.showerror("خطأ", "أدخل رقم الهاتف.", parent=ph_win)
            return
        clear_r()
        search_btn.config(state=tk.DISABLED, text="⏳ جارٍ الفحص...")
        insert_r(f"🔍 فحص الرقم: {number}...\n\n", "warning")

        def run():
            data = fetch_phone_info(number)
            clear_r()

            if data.get("error"):
                insert_r(f"❌ خطأ: {data['error']}\n", "invalid")
            else:
                insert_r(f"{'─'*52}\n", "divider")
                insert_r(f"  📞 {data.get('formatted', number)}\n", "title")
                insert_r(f"{'─'*52}\n\n", "divider")

                # Valid or not
                valid = data.get("valid")
                if valid is True:
                    insert_r("  ✅ الرقم صحيح وصالح\n\n", "valid")
                elif valid is False:
                    insert_r("  ❌ الرقم غير صحيح أو غير صالح\n\n", "invalid")

                if data.get("country"):
                    insert_r("  🌍 الدولة          : ", "key")
                    insert_r(f"{data['country']}\n", "value")

                if data.get("country_code"):
                    insert_r("  🔢 مفتاح الدولة    : ", "key")
                    insert_r(f"{data['country_code']}\n", "value")

                if data.get("location"):
                    insert_r("  📍 المنطقة         : ", "key")
                    insert_r(f"{data['location']}\n", "value")

                if data.get("carrier"):
                    insert_r("  📡 شركة الاتصالات  : ", "key")
                    insert_r(f"{data['carrier']}\n", "value")

                if data.get("type"):
                    insert_r("  📱 نوع الخط        : ", "key")
                    insert_r(f"{data['type']}\n", "value")

                if data.get("timezone"):
                    insert_r("  🕐 المنطقة الزمنية : ", "key")
                    insert_r(f"{data['timezone']}\n", "value")

                if data.get("national"):
                    insert_r("  📲 الرقم المحلي    : ", "key")
                    insert_r(f"{data['national']}\n", "value")

                if data.get("_no_lib"):
                    insert_r("\n⚠️ لمزيد من المعلومات ثبّت:\n", "warning")
                    insert_r("  pip install phonenumbers\n", "info")

                insert_r(f"\n  🔗 المصدر          : ", "key")
                insert_r(f"{data.get('source', 'غير معروف')}\n", "info")
                insert_r(f"\n{'─'*52}\n", "divider")

            search_btn.config(state=tk.NORMAL, text="🔍 فحص")

        threading.Thread(target=run, daemon=True).start()

    # ── Buttons ──
    btn_frame = tk.Frame(ph_win, bg="#0A1A0A")
    btn_frame.pack(fill=tk.X, padx=20, pady=10)

    search_btn = tk.Button(btn_frame, text="🔍 فحص",
                           command=do_lookup,
                           font=("Consolas", 12, "bold"),
                           bg="#16A34A", fg="white",
                           activebackground="#15803D", activeforeground="white",
                           bd=0, padx=25, pady=10, cursor="hand2")
    search_btn.pack(side=tk.LEFT, padx=5)

    clr_btn = tk.Button(btn_frame, text="🗑️ مسح",
                        command=clear_r,
                        font=("Consolas", 11),
                        bg="#0D2B0D", fg="#4ADE80",
                        activebackground="#1A3A1A", activeforeground="white",
                        bd=0, padx=15, pady=10, cursor="hand2")
    clr_btn.pack(side=tk.LEFT, padx=5)

    ph_entry.bind("<Return>", lambda e: do_lookup())
    ph_entry.focus()

    insert_r("أدخل رقم الهاتف مع مفتاح الدولة ثم اضغط 🔍 فحص\n\n", "warning")
    insert_r("💡 لنتائج أفضل ثبّت:\n", "key")
    insert_r("   pip install phonenumbers\n", "info")


def open_discord_window():
    """Open Discord lookup popup window with Bot Token support."""
    dc_win = tk.Toplevel(root)
    dc_win.title("🎮 Discord Lookup")
    dc_win.geometry("640x720")
    dc_win.configure(bg="#23272A")
    dc_win.resizable(False, False)

    # ── Header ──
    header = tk.Frame(dc_win, bg="#2C2F33", height=75)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(header, text="🎮  Discord Lookup",
             font=("Segoe UI", 16, "bold"), bg="#2C2F33", fg="white").pack(pady=8)
    tk.Label(header, text="أدخل Bot Token + User ID للحصول على كامل المعلومات",
             font=("Consolas", 8), bg="#2C2F33", fg="#99AAB5").pack()

    # ── Input Frame ──
    input_frame = tk.Frame(dc_win, bg="#2C2F33", pady=10)
    input_frame.pack(fill=tk.X, padx=20, pady=(10, 0))

    # ── User ID ──
    tk.Label(input_frame, text="🆔  User ID:",
             font=("Consolas", 10, "bold"), bg="#2C2F33", fg="#99AAB5").pack(anchor="w", padx=10)

    id_frame = tk.Frame(input_frame, bg="#40444B",
                        highlightthickness=2,
                        highlightbackground="#5865F2",
                        highlightcolor="#7289DA")
    id_frame.pack(fill=tk.X, padx=10, pady=(3, 8))

    tk.Label(id_frame, text="#", font=("Consolas", 13, "bold"),
             bg="#40444B", fg="#5865F2").pack(side=tk.LEFT, padx=(10, 0))
    dc_entry = tk.Entry(id_frame, font=("Consolas", 12),
                        bg="#40444B", fg="white",
                        insertbackground="#5865F2", bd=0, relief="flat")
    dc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=7)

    tk.Label(input_frame,
             text="💡 كيف تحصل على الـ ID: Discord ← Settings ← Advanced ← Developer Mode ← كليك يمين على مستخدم ← Copy User ID",
             font=("Consolas", 8), bg="#2C2F33", fg="#5865F2",
             wraplength=580, justify="right").pack(padx=10, pady=(0, 8))

    # ── Separator ──
    tk.Frame(input_frame, bg="#40444B", height=1).pack(fill=tk.X, padx=10, pady=5)

    # ── Bot Token ──
    token_header = tk.Frame(input_frame, bg="#2C2F33")
    token_header.pack(fill=tk.X, padx=10, pady=(5, 3))

    tk.Label(token_header, text="🤖  Bot Token:",
             font=("Consolas", 10, "bold"), bg="#2C2F33", fg="#FAA61A").pack(side=tk.LEFT)
    tk.Label(token_header, text="(مطلوب للحصول على كامل المعلومات)",
             font=("Consolas", 8), bg="#2C2F33", fg="#666").pack(side=tk.LEFT, padx=8)

    token_frame = tk.Frame(input_frame, bg="#40444B",
                           highlightthickness=2,
                           highlightbackground="#FAA61A",
                           highlightcolor="#FAA61A")
    token_frame.pack(fill=tk.X, padx=10, pady=(3, 5))

    tk.Label(token_frame, text="🔑", font=("Consolas", 12),
             bg="#40444B", fg="#FAA61A").pack(side=tk.LEFT, padx=(10, 0))
    token_entry = tk.Entry(token_frame, font=("Consolas", 11),
                           bg="#40444B", fg="#FAA61A",
                           insertbackground="#FAA61A",
                           show="•", bd=0, relief="flat")
    token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=7)

    # Show/hide token toggle
    show_var = tk.BooleanVar(value=False)
    def toggle_show():
        token_entry.config(show="" if show_var.get() else "•")
    show_cb = tk.Checkbutton(token_frame, text="إظهار", variable=show_var,
                             command=toggle_show,
                             bg="#40444B", fg="#99AAB5",
                             selectcolor="#40444B",
                             activebackground="#40444B",
                             font=("Consolas", 8), bd=0)
    show_cb.pack(side=tk.RIGHT, padx=5)

    tk.Label(input_frame,
             text="💡 كيف تحصل على Bot Token: discord.com/developers ← New Application ← Bot ← Reset Token",
             font=("Consolas", 8), bg="#2C2F33", fg="#FAA61A",
             wraplength=580, justify="right").pack(padx=10, pady=(2, 5))

    # ── Result ──
    result_frame = tk.Frame(dc_win, bg="#23272A")
    result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD,
                                             bg="#2C2F33", fg="#DCDDDE",
                                             font=("Consolas", 10),
                                             bd=0, relief="flat",
                                             padx=15, pady=10,
                                             state=tk.DISABLED)
    result_text.pack(fill=tk.BOTH, expand=True)
    result_text.tag_config("title",   foreground="#7289DA", font=("Consolas", 13, "bold"))
    result_text.tag_config("key",     foreground="#5865F2", font=("Consolas", 10, "bold"))
    result_text.tag_config("value",   foreground="#DCDDDE")
    result_text.tag_config("success", foreground="#43B581", font=("Consolas", 11, "bold"))
    result_text.tag_config("error",   foreground="#F04747", font=("Consolas", 11, "bold"))
    result_text.tag_config("warning", foreground="#FAA61A")
    result_text.tag_config("badge",   foreground="#FFD700")
    result_text.tag_config("divider", foreground="#40444B")
    result_text.tag_config("info",    foreground="#99AAB5")

    def insert_r(text, tag="value"):
        result_text.config(state=tk.NORMAL)
        result_text.insert(tk.END, text, tag)
        result_text.config(state=tk.DISABLED)

    def clear_r():
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.config(state=tk.DISABLED)

    def do_lookup():
        user_id = dc_entry.get().strip().lstrip("#@")
        token   = token_entry.get().strip()

        if not user_id:
            messagebox.showerror("خطأ", "أدخل User ID.", parent=dc_win)
            return
        if not token:
            messagebox.showerror("خطأ", "أدخل Bot Token أولاً.\nاذهب إلى discord.com/developers لإنشاء Bot.", parent=dc_win)
            return

        clear_r()
        search_btn.config(state=tk.DISABLED, text="⏳ جارٍ البحث...")
        insert_r(f"🔍 البحث عن User ID: {user_id}...\n\n", "warning")

        def run():
            try:
                # ── Discord Official API with Bot Token ──
                headers = {
                    "Authorization": f"Bot {token}",
                    "Content-Type": "application/json",
                    "User-Agent": "DiscordBot (https://github.com, 1.0)"
                }

                # Get user info
                resp = requests.get(
                    f"https://discord.com/api/v10/users/{user_id}",
                    headers=headers, timeout=10
                )

                clear_r()

                if resp.status_code == 401:
                    insert_r("❌ Bot Token خاطئ أو منتهي الصلاحية!\n\n", "error")
                    insert_r("💡 تأكد من Token الصحيح من discord.com/developers\n", "warning")
                    search_btn.config(state=tk.NORMAL, text="🔍 فحص")
                    return
                elif resp.status_code == 404:
                    insert_r(f"❌ المستخدم {user_id} غير موجود!\n", "error")
                    search_btn.config(state=tk.NORMAL, text="🔍 فحص")
                    return
                elif resp.status_code != 200:
                    insert_r(f"❌ خطأ من Discord API: HTTP {resp.status_code}\n", "error")
                    insert_r(f"   {resp.text[:200]}\n", "info")
                    search_btn.config(state=tk.NORMAL, text="🔍 فحص")
                    return

                u = resp.json()

                # ── Display Results ──
                insert_r(f"{'─'*52}\n", "divider")
                global_name = u.get("global_name") or u.get("username", "")
                insert_r(f"  {global_name}", "title")
                if u.get("bot"):
                    insert_r("  🤖 [BOT]", "warning")
                insert_r("\n", "title")
                insert_r(f"{'─'*52}\n\n", "divider")

                insert_r("  👤 Username       : ", "key")
                insert_r(f"@{u.get('username','')}\n", "value")

                if u.get("global_name") and u.get("global_name") != u.get("username"):
                    insert_r("  📛 Display Name   : ", "key")
                    insert_r(f"{u.get('global_name')}\n", "value")

                insert_r("  🆔 User ID         : ", "key")
                insert_r(f"{u.get('id','')}\n", "value")

                # Calculate account creation from snowflake ID
                try:
                    snowflake = int(u.get("id", 0))
                    timestamp = ((snowflake >> 22) + 1420070400000) / 1000
                    from datetime import datetime as dt
                    created = dt.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M UTC")
                    insert_r("  📅 تاريخ الإنشاء  : ", "key")
                    insert_r(f"{created}\n", "value")
                except: pass

                disc = u.get("discriminator", "0")
                if disc and disc != "0":
                    insert_r("  🔢 Discriminator  : ", "key")
                    insert_r(f"#{disc}\n", "value")

                insert_r("  🤖 نوع الحساب     : ", "key")
                insert_r(f"{'بوت (Bot)' if u.get('bot') else 'مستخدم عادي'}\n", "value")

                # Avatar
                if u.get("avatar"):
                    avatar_url = f"https://cdn.discordapp.com/avatars/{u['id']}/{u['avatar']}.png?size=256"
                    insert_r("  🖼️  الصورة الشخصية : ", "key")
                    insert_r(f"{avatar_url}\n", "info")

                # Banner
                if u.get("banner"):
                    banner_url = f"https://cdn.discordapp.com/banners/{u['id']}/{u['banner']}.png?size=512"
                    insert_r("  🎨 Banner          : ", "key")
                    insert_r(f"{banner_url}\n", "info")

                # Accent color
                if u.get("accent_color"):
                    hex_color = f"#{u['accent_color']:06X}"
                    insert_r("  🎨 لون الملف       : ", "key")
                    insert_r(f"{hex_color}\n", "value")

                # Badges
                badges = get_discord_badges(u.get("public_flags", 0))
                if badges:
                    insert_r("\n  🏅 الشارات         :\n", "key")
                    for b in badges:
                        insert_r(f"     {b}\n", "badge")

                # Profile link
                insert_r(f"\n{'─'*52}\n", "divider")
                insert_r("  🔗 الملف الشخصي   : ", "key")
                insert_r(f"https://discord.com/users/{u.get('id')}\n", "info")
                insert_r(f"{'─'*52}\n", "divider")

            except requests.exceptions.ConnectionError:
                clear_r()
                insert_r("❌ لا يوجد اتصال بالإنترنت\n", "error")
            except Exception as e:
                clear_r()
                insert_r(f"❌ خطأ غير متوقع: {e}\n", "error")

            search_btn.config(state=tk.NORMAL, text="🔍 فحص")

        threading.Thread(target=run, daemon=True).start()

    # ── Buttons ──
    btn_frame = tk.Frame(dc_win, bg="#23272A")
    btn_frame.pack(fill=tk.X, padx=20, pady=10)

    search_btn = tk.Button(btn_frame, text="🔍 فحص",
                           command=do_lookup,
                           font=("Consolas", 12, "bold"),
                           bg="#5865F2", fg="white",
                           activebackground="#4752C4", activeforeground="white",
                           bd=0, padx=25, pady=10, cursor="hand2")
    search_btn.pack(side=tk.LEFT, padx=5)

    open_btn = tk.Button(btn_frame, text="🌐 فتح في Discord",
                         command=lambda: webbrowser.open(f"https://discord.com/users/{dc_entry.get().strip()}") if dc_entry.get().strip() else None,
                         font=("Consolas", 11),
                         bg="#40444B", fg="white",
                         activebackground="#2C2F33", activeforeground="white",
                         bd=0, padx=15, pady=10, cursor="hand2")
    open_btn.pack(side=tk.LEFT, padx=5)

    clr_btn = tk.Button(btn_frame, text="🗑️ مسح",
                        command=clear_r,
                        font=("Consolas", 11),
                        bg="#2C2F33", fg="#99AAB5",
                        activebackground="#40444B", activeforeground="white",
                        bd=0, padx=15, pady=10, cursor="hand2")
    clr_btn.pack(side=tk.LEFT, padx=5)

    dc_entry.bind("<Return>", lambda e: do_lookup())
    dc_entry.focus()

    insert_r("أدخل User ID و Bot Token ثم اضغط 🔍 فحص\n\n", "warning")
    insert_r("🔑 للحصول على Bot Token:\n", "key")
    insert_r("   1. اذهب إلى: discord.com/developers/applications\n", "info")
    insert_r("   2. New Application ← Bot ← Reset Token\n", "info")
    insert_r("   3. انسخ الـ Token والصقه هنا\n\n", "info")
    insert_r("⚠️ لا تشارك الـ Token مع أحد!\n", "warning")



def fetch_instagram_info(username):
    """Fetch public Instagram profile info using multiple methods."""
    import re

    result = {"exists": True, "username": username, "url": f"https://www.instagram.com/{username}/"}

    # ── Method 1: Instagram JSON API endpoint ──
    try:
        headers = {
            "User-Agent": "Instagram 123.0.0.21.114 Android",
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "x-ig-app-id": "936619743392459",
        }
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return {"exists": False, "username": username}
        if resp.status_code == 200:
            data = resp.json()
            user = data.get("data", {}).get("user", {})
            if user:
                result["full_name"]  = user.get("full_name", "")
                result["biography"]  = user.get("biography", "").replace("\\n", "\n")
                result["followers"]  = user.get("edge_followed_by", {}).get("count")
                result["following"]  = user.get("edge_follow", {}).get("count")
                result["posts"]      = user.get("edge_owner_to_timeline_media", {}).get("count")
                result["is_private"] = user.get("is_private")
                result["is_verified"]= user.get("is_verified")
                result["external_url"]= user.get("external_url", "")
                result["category"]   = user.get("category_name", "")
                result["profile_pic"]= user.get("profile_pic_url_hd", "")
                return result
    except Exception:
        pass

    # ── Method 2: oEmbed API (public accounts only) ──
    try:
        oembed_url = f"https://www.instagram.com/oembed/?url=https://www.instagram.com/{username}/"
        headers2 = {"User-Agent": "Mozilla/5.0"}
        resp2 = requests.get(oembed_url, headers=headers2, timeout=8)
        if resp2.status_code == 200:
            d = resp2.json()
            result["full_name"] = d.get("author_name", "")
            # oEmbed doesn't give followers, mark partial
            result["_partial"] = True
            return result
        elif resp2.status_code == 404:
            return {"exists": False, "username": username}
    except Exception:
        pass

    # ── Method 3: HTML scrape with mobile UA ──
    try:
        headers3 = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml",
        }
        url3 = f"https://www.instagram.com/{username}/"
        resp3 = requests.get(url3, headers=headers3, timeout=10)
        html = resp3.text

        if resp3.status_code == 404 or "Page Not Found" in html:
            return {"exists": False, "username": username}

        for pattern, key in [
            (r'"full_name":"([^"]+)"',        "full_name"),
            (r'"biography":"([^"]*)"',         "biography"),
            (r'"is_private":(true|false)',     "is_private_str"),
            (r'"is_verified":(true|false)',    "is_verified_str"),
            (r'"edge_followed_by":\{"count":(\d+)\}', "followers_str"),
            (r'"edge_follow":\{"count":(\d+)\}',      "following_str"),
            (r'"edge_owner_to_timeline_media":\{"count":(\d+)', "posts_str"),
            (r'"external_url":"([^"]*)"',      "external_url"),
            (r'"category_name":"([^"]*)"',     "category"),
        ]:
            m = re.search(pattern, html)
            if m:
                result[key] = m.group(1)

        # Convert string booleans and numbers
        if "is_private_str"  in result: result["is_private"]  = result.pop("is_private_str")  == "true"
        if "is_verified_str" in result: result["is_verified"] = result.pop("is_verified_str") == "true"
        if "followers_str"   in result: result["followers"]   = int(result.pop("followers_str"))
        if "following_str"   in result: result["following"]   = int(result.pop("following_str"))
        if "posts_str"       in result: result["posts"]       = int(result.pop("posts_str"))

        return result

    except requests.exceptions.ConnectionError:
        return {"exists": None, "error": "لا يوجد اتصال بالإنترنت"}
    except Exception as e:
        return {"exists": None, "error": str(e)}


def format_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def open_instagram_window():
    """Open Instagram lookup popup window."""
    ig_win = tk.Toplevel(root)
    ig_win.title("📸 Instagram Lookup")
    ig_win.geometry("600x620")
    ig_win.configure(bg="#0A0A0A")
    ig_win.resizable(False, False)

    # ── Header ──
    header = tk.Frame(ig_win, bg="#1A1A1A", height=80)
    header.pack(fill=tk.X)
    header.pack_propagate(False)

    # Instagram gradient-like label
    tk.Label(header, text="📸  Instagram Lookup",
             font=("Segoe UI", 16, "bold"), bg="#1A1A1A", fg="white").pack(pady=10)
    tk.Label(header, text="فحص الحسابات العامة فقط • للأغراض التعليمية",
             font=("Consolas", 8), bg="#1A1A1A", fg="#666").pack()

    # ── Input area ──
    input_frame = tk.Frame(ig_win, bg="#141414", pady=20)
    input_frame.pack(fill=tk.X, padx=20, pady=10)

    tk.Label(input_frame, text="اسم المستخدم (Username):",
             font=("Consolas", 10), bg="#141414", fg="#AAAAAA").pack(anchor="w", padx=10)

    entry_frame = tk.Frame(input_frame, bg="#222222", highlightthickness=2,
                           highlightbackground="#C13584", highlightcolor="#E1306C")
    entry_frame.pack(fill=tk.X, padx=10, pady=5)

    tk.Label(entry_frame, text="@", font=("Consolas", 14, "bold"),
             bg="#222222", fg="#C13584").pack(side=tk.LEFT, padx=(10, 0))

    ig_entry = tk.Entry(entry_frame, font=("Consolas", 13), bg="#222222", fg="white",
                        insertbackground="#C13584", bd=0, relief="flat")
    ig_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=8)

    # ── Result area ──
    result_frame = tk.Frame(ig_win, bg="#0A0A0A")
    result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD,
                                             bg="#111111", fg="#E5E5E5",
                                             font=("Consolas", 10),
                                             bd=0, relief="flat",
                                             padx=15, pady=10,
                                             state=tk.DISABLED)
    result_text.pack(fill=tk.BOTH, expand=True)
    result_text.tag_config("title",    foreground="#E1306C", font=("Consolas", 13, "bold"))
    result_text.tag_config("key",      foreground="#C13584", font=("Consolas", 10, "bold"))
    result_text.tag_config("value",    foreground="#F0F0F0")
    result_text.tag_config("success",  foreground="#22C55E", font=("Consolas", 11, "bold"))
    result_text.tag_config("error",    foreground="#EF4444", font=("Consolas", 11, "bold"))
    result_text.tag_config("warning",  foreground="#F59E0B")
    result_text.tag_config("link",     foreground="#60A5FA", font=("Consolas", 10, "underline"))
    result_text.tag_config("divider",  foreground="#333333")

    def insert_result(text, tag="value"):
        result_text.config(state=tk.NORMAL)
        result_text.insert(tk.END, text, tag)
        result_text.config(state=tk.DISABLED)

    def clear_result():
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.config(state=tk.DISABLED)

    def do_lookup():
        username = ig_entry.get().strip().lstrip("@")
        if not username:
            messagebox.showerror("خطأ", "أدخل اسم المستخدم.", parent=ig_win)
            return

        clear_result()
        search_btn.config(state=tk.DISABLED, text="⏳ جارٍ البحث...")
        insert_result(f"🔍 البحث عن @{username}...\n\n", "warning")

        def run():
            data = fetch_instagram_info(username)
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.config(state=tk.DISABLED)

            if data.get("exists") is False:
                insert_result(f"❌ الحساب @{username} غير موجود على Instagram.\n", "error")
            elif data.get("exists") is None:
                insert_result(f"⚠️ تعذر الوصول: {data.get('error','خطأ غير معروف')}\n", "error")
                insert_result("\nقد يكون Instagram يحظر الطلبات المباشرة.\nجرب مرة أخرى أو افتح الحساب في المتصفح.\n", "warning")
            else:
                # Header
                verified = " ✅" if data.get("is_verified") else ""
                private = " 🔒" if data.get("is_private") else " 🌍"
                insert_result(f"{'─'*50}\n", "divider")
                insert_result(f"  @{data['username']}{verified}{private}\n", "title")
                insert_result(f"{'─'*50}\n\n", "divider")

                if data.get("full_name"):
                    insert_result("  الاسم الكامل  : ", "key")
                    insert_result(f"{data['full_name']}\n", "value")

                if data.get("is_verified") is not None:
                    insert_result("  موثَّق        : ", "key")
                    insert_result(f"{'✅ نعم' if data['is_verified'] else '❌ لا'}\n", "value")

                if data.get("is_private") is not None:
                    insert_result("  الخصوصية      : ", "key")
                    insert_result(f"{'🔒 خاص (Private)' if data['is_private'] else '🌍 عام (Public)'}\n", "value")

                if data.get("followers") is not None:
                    insert_result("  المتابعون     : ", "key")
                    insert_result(f"{format_number(data['followers'])} ({data['followers']:,})\n", "value")

                if data.get("following") is not None:
                    insert_result("  يتابع         : ", "key")
                    insert_result(f"{format_number(data['following'])} ({data['following']:,})\n", "value")

                if data.get("posts") is not None:
                    insert_result("  المنشورات     : ", "key")
                    insert_result(f"{data['posts']:,}\n", "value")

                if data.get("category"):
                    insert_result("  التصنيف       : ", "key")
                    insert_result(f"{data['category']}\n", "value")

                if data.get("biography"):
                    insert_result("\n  البايو        :\n", "key")
                    insert_result(f"  {data['biography']}\n", "value")

                if data.get("external_url"):
                    insert_result("\n  الرابط الخارجي: ", "key")
                    insert_result(f"{data['external_url']}\n", "link")

                insert_result(f"\n{'─'*50}\n", "divider")
                insert_result("  🔗 رابط الحساب: ", "key")
                insert_result(f"{data['url']}\n", "link")
                insert_result(f"{'─'*50}\n", "divider")

            search_btn.config(state=tk.NORMAL, text="🔍 فحص")

        threading.Thread(target=run, daemon=True).start()

    # ── Buttons ──
    btn_frame = tk.Frame(ig_win, bg="#0A0A0A")
    btn_frame.pack(fill=tk.X, padx=20, pady=10)

    search_btn = tk.Button(btn_frame, text="🔍 فحص",
                           command=do_lookup,
                           font=("Consolas", 12, "bold"),
                           bg="#C13584", fg="white",
                           activebackground="#E1306C", activeforeground="white",
                           bd=0, padx=25, pady=10, cursor="hand2")
    search_btn.pack(side=tk.LEFT, padx=5)

    open_btn = tk.Button(btn_frame, text="🌐 فتح في المتصفح",
                         command=lambda: webbrowser.open(f"https://www.instagram.com/{ig_entry.get().strip().lstrip('@')}/") if ig_entry.get().strip() else None,
                         font=("Consolas", 11),
                         bg="#2563EB", fg="white",
                         activebackground="#1D4ED8", activeforeground="white",
                         bd=0, padx=15, pady=10, cursor="hand2")
    open_btn.pack(side=tk.LEFT, padx=5)

    clear_btn = tk.Button(btn_frame, text="🗑️ مسح",
                          command=clear_result,
                          font=("Consolas", 11),
                          bg="#1A1A1A", fg="#888",
                          activebackground="#222", activeforeground="white",
                          bd=0, padx=15, pady=10, cursor="hand2")
    clear_btn.pack(side=tk.LEFT, padx=5)

    # Bind Enter key
    ig_entry.bind("<Return>", lambda e: do_lookup())
    ig_entry.focus()

    insert_result("أدخل اسم المستخدم واضغط 'فحص' أو Enter\n\n", "warning")
    insert_result("⚠️ ملاحظة: يعمل على الحسابات العامة فقط.\n", "divider")
    insert_result("Instagram قد يحجب الطلبات أحياناً - هذا طبيعي.\n", "divider")


# ═══════════════════════════════════════════
# GUI SETUP
# ═══════════════════════════════════════════
root = tk.Tk()
root.title(f"FLASH Control Center v5.0  ⚡  |  {CURRENT_USER}")
root.geometry("1440x900")
root.minsize(1100, 700)
root.configure(bg=BG_MAIN)
root.protocol("WM_DELETE_WINDOW", lambda: sys.exit())

# ── SIDEBAR ──────────────────────────────
sidebar = tk.Frame(root, bg=BG_SIDEBAR, width=220)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
sidebar.pack_propagate(False)

logo_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
logo_frame.pack(fill=tk.X, pady=(30, 10))

tk.Label(logo_frame, text="⚡", font=("Segoe UI", 36), bg=BG_SIDEBAR, fg=ACCENT_BLUE).pack()
tk.Label(logo_frame, text="FLASH", font=("Consolas", 18, "bold"), bg=BG_SIDEBAR, fg="white").pack()
tk.Label(logo_frame, text="Control Center", font=("Consolas", 9), bg=BG_SIDEBAR, fg="#64748B").pack()

tk.Frame(sidebar, bg="#2D2D4E", height=1).pack(fill=tk.X, padx=20, pady=20)

nav_items = [
    ("🔍  فحص شامل",     ACCENT_BLUE),
    ("🌍  خريطة الهدف",  "#7C3AED"),
    ("⚡  مسح المنافذ",   ACCENT_ORANGE),
    ("📜  WHOIS",         ACCENT_GREEN),
]
for label, color in nav_items:
    btn = tk.Label(sidebar, text=label, font=("Consolas", 11), bg=BG_SIDEBAR, fg="#94A3B8",
                   cursor="hand2", anchor="w", padx=20, pady=8)
    btn.pack(fill=tk.X)
    btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(fg=c, bg="#252545"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(fg="#94A3B8", bg=BG_SIDEBAR))

# Instagram Button in Sidebar
tk.Frame(sidebar, bg="#2D2D4E", height=1).pack(fill=tk.X, padx=20, pady=10)
insta_btn = tk.Button(sidebar, text="📸  Instagram",
                       font=("Consolas", 11, "bold"),
                       bg="#C13584", fg="white",
                       activebackground="#E1306C", activeforeground="white",
                       bd=0, padx=20, pady=10, cursor="hand2", anchor="w",
                       command=lambda: open_instagram_window())
insta_btn.pack(fill=tk.X, padx=10, pady=5)

# Discord Button in Sidebar
discord_btn = tk.Button(sidebar, text="🎮  Discord",
                        font=("Consolas", 11, "bold"),
                        bg="#5865F2", fg="white",
                        activebackground="#4752C4", activeforeground="white",
                        bd=0, padx=20, pady=10, cursor="hand2", anchor="w",
                        command=lambda: open_discord_window())
discord_btn.pack(fill=tk.X, padx=10, pady=5)

# Phone Button
phone_btn = tk.Button(sidebar, text="📞  Phone Lookup",
                      font=("Consolas", 11, "bold"),
                      bg="#16A34A", fg="white",
                      activebackground="#15803D", activeforeground="white",
                      bd=0, padx=20, pady=10, cursor="hand2", anchor="w",
                      command=lambda: open_phone_window())
phone_btn.pack(fill=tk.X, padx=10, pady=5)

tk.Frame(sidebar, bg="#2D2D4E", height=1).pack(fill=tk.X, padx=20, pady=20)

version_label = tk.Label(sidebar, text="v5.0 • 2026", font=("Consolas", 8),
                         bg=BG_SIDEBAR, fg="#475569")
version_label.pack(side=tk.BOTTOM, pady=15)

# ── MAIN CONTENT ─────────────────────────
content = tk.Frame(root, bg=BG_MAIN)
content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# ── TOPBAR ───────────────────────────────
topbar = tk.Frame(content, bg=BG_CARD, height=65)
topbar.pack(fill=tk.X)
topbar.pack_propagate(False)

tk.Frame(topbar, bg=ACCENT_BLUE, width=4).pack(side=tk.LEFT, fill=tk.Y)

tk.Label(topbar, text="لوحة الاستخبارات والفحص الأمني",
         font=("Consolas", 14, "bold"), bg=BG_CARD, fg=TEXT_DARK).pack(side=tk.LEFT, padx=20)

status_label = tk.Label(topbar, text="● جاهز", font=("Consolas", 10),
                        bg=BG_CARD, fg=ACCENT_GREEN)
status_label.pack(side=tk.RIGHT, padx=20)

# ── INPUT CARD ───────────────────────────
input_card = tk.Frame(content, bg=BG_CARD, relief="flat")
input_card.pack(fill=tk.X, padx=20, pady=(15, 5))

tk.Frame(input_card, bg=ACCENT_BLUE, height=3).pack(fill=tk.X)

input_inner = tk.Frame(input_card, bg=BG_CARD)
input_inner.pack(fill=tk.X, padx=20, pady=15)

tk.Label(input_inner, text="عنوان IP أو النطاق المستهدف:",
         font=("Consolas", 10, "bold"), bg=BG_CARD, fg=TEXT_MID).pack(side=tk.LEFT, padx=(0, 10))

recon_target_entry = tk.Entry(input_inner, width=35, font=("Consolas", 12),
                               bg=BG_MAIN, fg=TEXT_DARK, insertbackground=ACCENT_BLUE,
                               bd=0, relief="flat", highlightthickness=2,
                               highlightbackground=BORDER, highlightcolor=ACCENT_BLUE)
recon_target_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=6)
recon_target_entry.insert(0, "مثال: 8.8.8.8 أو google.com")
recon_target_entry.config(fg=TEXT_LIGHT)

def on_entry_click(e):
    if recon_target_entry.get() in ["مثال: 8.8.8.8 أو google.com", ""]:
        recon_target_entry.delete(0, tk.END)
        recon_target_entry.config(fg=TEXT_DARK)
recon_target_entry.bind("<FocusIn>", on_entry_click)

recon_button = tk.Button(input_inner, text="🚀 فحص شامل",
                          command=perform_full_recon_gui,
                          font=("Consolas", 11, "bold"),
                          bg=ACCENT_BLUE, fg="white",
                          activebackground="#1D4ED8", activeforeground="white",
                          bd=0, padx=20, pady=8, cursor="hand2")
recon_button.pack(side=tk.LEFT, padx=5)

open_map_button = tk.Button(input_inner, text="🌍 الخريطة",
                            command=open_map_location_gui,
                            font=("Consolas", 11, "bold"),
                            bg=ACCENT_GREEN, fg="white",
                            activebackground="#15803D", activeforeground="white",
                            bd=0, padx=15, pady=8, cursor="hand2",
                            state=tk.DISABLED)
open_map_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(input_inner, text="🗑️ مسح",
                          command=clear_console,
                          font=("Consolas", 11),
                          bg="#F1F5F9", fg=TEXT_MID,
                          activebackground=BORDER, activeforeground=TEXT_DARK,
                          bd=0, padx=15, pady=8, cursor="hand2")
clear_button.pack(side=tk.LEFT, padx=5)

# ── PROGRESS BAR ─────────────────────────
progress_frame = tk.Frame(content, bg=BG_MAIN)
progress_frame.pack(fill=tk.X, padx=20, pady=(5, 0))

style_ttk = ttk.Style()
style_ttk.theme_use('clam')
style_ttk.configure("Blue.Horizontal.TProgressbar",
                     troughcolor=BORDER, background=ACCENT_BLUE,
                     thickness=6, borderwidth=0)

progress_bar = ttk.Progressbar(progress_frame, style="Blue.Horizontal.TProgressbar",
                                orient="horizontal", length=100, mode="determinate")
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

progress_label = tk.Label(progress_frame, text="0%", font=("Consolas", 9),
                          bg=BG_MAIN, fg=TEXT_MID, width=5)
progress_label.pack(side=tk.LEFT, padx=5)

# ── CONSOLE ──────────────────────────────
console_frame = tk.Frame(content, bg=BG_MAIN)
console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

console_header = tk.Frame(console_frame, bg=CONSOLE_BG)
console_header.pack(fill=tk.X)

tk.Label(console_header, text="● ● ●", font=("Consolas", 10),
         bg=CONSOLE_BG, fg="#475569").pack(side=tk.LEFT, padx=12, pady=8)
tk.Label(console_header, text="مخرجات الفحص والاستخبارات",
         font=("Consolas", 10, "bold"), bg=CONSOLE_BG, fg="#64748B").pack(side=tk.LEFT)

console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, state=tk.DISABLED,
                                          bg=CONSOLE_BG, fg=CONSOLE_FG,
                                          font=("Consolas", 10),
                                          insertbackground=ACCENT_BLUE,
                                          selectbackground=ACCENT_BLUE,
                                          selectforeground="white",
                                          bd=0, relief="flat",
                                          padx=15, pady=10)
console_text.pack(fill=tk.BOTH, expand=True)

# Console Tags
console_text.tag_config("error",     foreground="#EF4444")
console_text.tag_config("success",   foreground="#22C55E")
console_text.tag_config("header",    foreground=ACCENT_BLUE,   font=("Consolas", 12, "bold"))
console_text.tag_config("section",   foreground="#F59E0B",      font=("Consolas", 11, "bold"))
console_text.tag_config("separator", foreground="#334155")
console_text.tag_config("info",      foreground="#94A3B8")
console_text.tag_config("normal",    foreground=CONSOLE_FG)

# Welcome Message
update_console_status(f"  ⚡ FLASH Control Center v5.0  |  أهلاً {CURRENT_USER}!", style_tag="header")
update_console_status("  أدخل IP أو نطاق الهدف ثم اضغط 'فحص شامل'.\n", style_tag="info")

if not folium:
    update_console_status("  ⚠️ تحذير: Folium غير مثبت. ميزة الخريطة معطلة. (pip install folium)", style_tag="error")

root.mainloop()

