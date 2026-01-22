# 📟 3615 LeChat : Le Chatbot LLM sur Minitel avec Jetson Nano

**3615 LeChat** est un projet de "Retro-Computing" qui redonne vie au célèbre terminal français des années 80 : le **Minitel**. Grâce à une carte NVIDIA Jetson Nano et au moteur d'inférence **Ollama**, ce projet transforme un Minitel en une interface de chat intelligente, capable de converser en temps réel avec des modèles comme Mistral ou Ministral.

Ce projet a été conçu par Alban Trentesaux et Mathis Brebion, étudiants en 5ème année à l'école d'ingénieurs **UniLaSalle Amiens**.

---

## ✨ Fonctionnalités

* **Connexion Authentique** : Simulation d'une connexion télématique avec saisie du service (ex: `3615 LECHAT`).
* **IA Moderne** : Intégration complète avec **Ollama** pour des réponses générées localement.
* **Pagination Intelligente** : Gestion automatique de l'écran (40x24) avec détection de la touche **[SUITE]** pour éviter le débordement de texte.
* **Filtre Vidéotex** : Conversion dynamique des caractères spéciaux et accentués pour une compatibilité parfaite avec la norme CEPT2 du Minitel.
* **Gestion du Clavier** : Support des touches physiques **[ENVOI]**, **[CORRECTION]**, **[SOMMAIRE]** et **[SUITE]**.
* **Robustesse** : Détection automatique de l'allumage/extinction du Minitel avec redémarrage du cycle logiciel.

---

## 🛠 Matériel Requis

1. **Un Minitel** (Modèle 1, 1B ou 2) avec prise DIN 5 broches à l'arrière.
2. **Une carte Jetson Nano** (ou un Raspberry Pi / PC Linux).
3. **Un adaptateur USB-Série** (TTL 5V).
* *Note : Un montage avec inverseur logique est nécessaire pour adapter les signaux RX/TX du Minitel.*


4. **Câble DIN 5 broches vers USB-Série**.

---

## 🚀 Installation

### 1. Prérequis Logiciels

Assurez-vous d'avoir Python 3.8+ installé.

```bash
# Installation des dépendances Python
pip install pyserial requests

```

### 2. Installation d'Ollama

Installez Ollama sur votre machine hôte (Jetson Nano ou autre) :

```bash
curl -fsSL https://ollama.com/install.sh | sh

```

Puis, téléchargez le modèle par défaut utilisé dans le script :

```bash
ollama pull ministral-3:3b

```

### 3. Configuration du Port Série

Le script scanne automatiquement les ports. Sur Linux (Jetson), assurez-vous que votre utilisateur a les droits d'accès :

```bash
sudo usermod -a -G dialout $USER
# Redémarrez votre session après cette commande

```

---

## 💻 Utilisation

1. Reliez le Minitel à votre Jetson Nano via l'adaptateur.
2. Lancez le script :
```bash
python Chatbot.py

```
3. Allumez le Minitel.


4. **Sur le Minitel** :
* Le script attend un signal (appuyez sur une touche si rien ne se passe).
* Tapez `3615 LECHAT` pour vous connecter.
* Saisissez votre nom.
* Posez vos questions !



### Commandes Minitel spéciales :

* **[SOMMAIRE]** : Efface l'écran et réinitialise l'interface de chat.
* **[SUITE]** : Affiche la suite d'une réponse longue.
* **Taper `exit` : Déclenche l'arrêt sécurisé (`shutdown`) de la Jetson Nano.

---

## ⚙️ Structure du Code

* `scan_serial_port()` : Identifie l'adaptateur USB-Série selon l'OS.
* `preload_model()` : Charge le LLM en VRAM dès le lancement pour éviter l'attente au premier message.
* `get_input()` : Gère la lecture bufferisée et les séquences d'échappement Videotex (`0x13`).
* `send_with_count()` : Moteur de rendu qui gère le retour à la ligne automatique (40 col) et la pagination.
* `filter_text()` : Normalise l'Unicode vers l'ASCII pour l'affichage vintage.

---

## 🎓 Crédits

Projet réalisé dans le cadre du cursus Ingénieur RIOC (Réseuax Informatiques et Objets Connectés) à **UniLaSalle Amiens** (ex. **ESIEE-Amiens**).

* **Développeurs** : Alban Trentesaux & Mathis Brebion (RIOC-FISA-2026).
* **Technologies** : Python, Ollama, Serial Videotex.