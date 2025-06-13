# 🛑 Rogue Access Point – Captive Portal & Phishing

> Projet réalisé par **Anis Slimani**  
> ESGI - Cybersécurité – Mai 2025

---

## 🎯 Objectif du Projet

Ce projet démontre une attaque réaliste par **Rogue Access Point** simulant un Wi-Fi gratuit dans un lieu public (ex: McDonald's), redirigeant la victime vers un **portail captif de phishing**, et lui donnant ensuite un **accès Internet réel**.

---

## 🧠 Fonctionnement Global

Le script `rogue_ap.py` automatise l’attaque :

- Crée un **faux point d’accès Wi-Fi** (`McDo_FREE_WIFI`)
- Configure **dnsmasq** pour le DHCP & DNS
- Lance un **portail captif** avec Flask
- Capture les identifiants (email + mot de passe)
- Autorise l’accès Internet à la victime après authentification

---

## 🖥️ Interfaces Réseau

| Rôle              | Interface par défaut |
|-------------------|----------------------|
| Point d'accès Wi-Fi | `wlan0`              |
| Accès Internet     | `eth0`               |

---

## 🗂️ Arborescence du Projet
```text
RogueAP/
├── rogue_ap.py # Script principal
├── hostapd.conf # Config AP Wi-Fi
├── dnsmasq.conf # Config DHCP & DNS
├── captured.txt # Identifiants capturés
└── templates/
├── login.html # Page de phishing
└── logo.png # Logo McDonald's
```


---

## ⚙️ Dépendances


Installez les dépendances nécessaires :

```
sudo apt install hostapd dnsmasq net-tools netifaces python3-flask
```
```

🚀 Lancement Rapide
1. Adapter les interfaces dans le script
Dans rogue_ap.py :

interface = "wlan0"        # Interface Wi-Fi (ligne ~327)
internet_iface = "eth0"    # Interface Internet dans setup_ap()
gateway = "192.168.1.1"    # Passerelle si besoin
```

2. Lancer le script
```

sudo systemctl stop NetworkManager   # (important)
sudo python3 rogue_ap.py
```
```

🔬 Scénario de l'Attaque
1.La victime voit un Wi-Fi "McDo_FREE_WIFI"
2.Elle se connecte → redirection automatique vers /login
3.Elle entre son email/mot de passe pour "activer Internet"
4.Les identifiants sont enregistrés dans captured.txt
5.L'accès Internet est ouvert automatiquement
6.Elle est redirigée vers le vrai site : https://www.mcdonalds.fr

📸 Captures & Vidéo
📽️ Démo vidéo du projet (YouTube) :

👉 https://youtu.be/g7vIihK-B5Q?si=aruy5bFbdhsVp2ti


📁 Le fichier captured.txt contient :

Email saisi
Mot de passe
IP de la victime
Date et heure

🧼 Nettoyage Post-Test

# Arrêter le script
Ctrl + C

# Réactiver NetworkManager
sudo systemctl start NetworkManager

🛡️ Disclaimer
⚠️ Ce projet est à but éducatif uniquement.
Toute utilisation non autorisée dans un environnement réel est illégale et condamnable par la loi.

📎 Auteurs
👨‍💻 Slimani Anis



---
