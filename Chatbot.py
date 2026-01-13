import json

import serial
import time
import sys
import serial.tools.list_ports
import requests

BAUD_RATE = 1200  # Vitesse standard Minitel mode videotexte


class MinitelResetException(Exception):
    """Exception pour forcer le redémarrage du script"""
    pass

def scan_serial_port():
    """Scanne les ports série pour trouver un Minitel connecté"""
    if sys.platform.startswith('darwin'):  # macOS
        print("Scan des ports série sur macOS...")
        prefixes = ["/dev/cu.usbserial-", "/dev/cu.usbmodem"]
    elif sys.platform.startswith('linux'):  # Linux
        print("Scan des ports série sur Linux...")
        prefixes = ["/dev/cuUSB", "/dev/cuACM"]
    else:
        print("Scan des ports série sur Windows...")
        prefixes = ["COM"] # Windows

    ports_disponibles = serial.tools.list_ports.comports()
    print("Ports série disponibles :")
    for port in ports_disponibles:
        print(f" - {port.device}: {port.description}")
    serial_port = []

    for port in ports_disponibles:
        # On vérifie si le port commence par l'un des préfixes connus
        for prefix in prefixes:
            if port.device.startswith(prefix):
                serial_port.append(port.device)

    print ("Ports série détectés pour Minitel : ", serial_port)

    return serial_port[0]
class MinitelChatbot:
    def __init__(self):
        # Configuration spécifique au Minitel : 7 bits, Parité Paire, 1 bit de stop
        self.ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1
        )

        # Codes de contrôle Videotex (norme CEPT2)
        self.CLEAR_SCREEN = b'\x0C'
        self.CURSOR_HOME = b'\x1E'
        self.GREEN_TEXT = b'\x1B\x42'
        self.WHITE_TEXT = b'\x1B\x47'
        self.CYAN_TEXT = b'\x1B\x46'
        self.BOLD_TEXT = b'\x1B\x45'


    def send(self, *args):
        """Envoie des données (bytes ou str) au Minitel"""
        for data in args:
            if isinstance(data, str):
                data = data.encode('ascii', errors='replace')
            self.ser.write(data)

    def move_cursor(self, row, col):
        """Positionne le curseur : Ligne (1-24), Colonne (1-40)"""
        self.send(b'\x1B\x59' + bytes([row + 31]) + bytes([col + 31]))

    def get_input(self):
        """Lit les caractères avec gestion de votre touche Envoi (13 41)"""
        user_input = ""
        while True:
            char = self.ser.read(1)
            if not char:
                continue

            # Détection des touches de fonction (Préfixe 0x13 sur votre modèle)
            if char == b'\x13':
                next_char = self.ser.read(1)
                if next_char == b'A':  # ENVOI
                    self.send("\n\r")
                    return user_input
                elif next_char == b'G':  # CORRECTION
                    if len(user_input) > 0:
                        user_input = user_input[:-1]
                        self.send(b'\x08 \x08')
                continue

            # Caractères normaux
            try:
                if ord(char) >= 32:
                    decoded = char.decode('ascii')
                    user_input += decoded
            except:
                pass

    def connexion_simulation(self):
        self.send(self.CLEAR_SCREEN)
        self.send("Entrez votre requete minitel\n\r")
        input=self.get_input()
        if input == "3615 LECHAT":
            self.send("\r\nConnexion au 3615 LeChat...\r\n")
            time.sleep(1)
            self.send("\r\nConnexion etablie !\r\n")
            time.sleep(0.5)
        else:
            self.send("\r\nNumero inconnu. Veuillez reessayer.\r\n")
            time.sleep(1)
            self.connexion_simulation()

        USERNAME = self.show_welcome_page()
        return USERNAME

    def show_welcome_page(self):
        self.send(self.CLEAR_SCREEN)
        time.sleep(0.2)

        # En-tête
        self.send(self.CYAN_TEXT)
        self.send("--- BIENVENUE SUR 3615 LECHAT ---\n\r")

        # Consigne
        self.send(self.WHITE_TEXT)
        self.send("Veuillez entrer votre nom pour commencer :\n\r")

        # Ligne de séparation
        self.send("-" * 40 + "\n\r")

        # Invite de saisie
        self.send(self.GREEN_TEXT)
        self.send("NOM : ")

        # Récupération de la saisie
        nom = self.get_input()

        # Si l'utilisateur n'a rien tapé, on renvoie "Anonyme"
        return nom if nom.strip() != "" else "Anonyme"

    def setup_ui(self):
        """Initialise l'interface visuelle"""
        self.send(self.CLEAR_SCREEN)
        time.sleep(0.2)

        # Correction : On concatène des bytes avec des bytes (notés b'...')
        # Ou on appelle send séparément pour chaque élément
        self.send(self.CYAN_TEXT)
        self.send("--- 3615 LeChat ---\n\r")

        self.send(self.WHITE_TEXT)
        self.send("Posez votre question ci-dessous :\n\r")
        self.send("-" * 40 + "\n\r")

    def get_input(self):
        """Lit les caractères et gère les séquences spécifiques"""
        user_input = ""
        while True:
            char = self.ser.read(1)
            if not char:
                continue

            # 1. Détection de déconnexion / extinction (Caractère NULL)
            if char == b'\x00':
                print("Signal de déconnexion détecté (0x00)...")
                # On vide le buffer pour éviter les faux positifs
                self.ser.reset_input_buffer()
                raise MinitelResetException("Minitel éteint ou déconnecté")

            # 2. Détection du préfixe de touche de fonction (0x13)
            if char == b'\x13':
                next_char = self.ser.read(1)

                # Touche ENVOI (13 41)
                if next_char == b'A':
                    self.send("\n\r")
                    return user_input

                # Touche CORRECTION (13 47) - Vérifiez si c'est 'G' sur votre Minitel
                elif next_char == b'G' or next_char == b'\x47':
                    if len(user_input) > 0:
                        user_input = user_input[:-1]
                        self.send(b'\x08 \x08')
                continue

            # 3. Echo local et stockage du texte
            try:
                if ord(char) >= 32:
                    decoded = char.decode('ascii')
                    # self.send(char) # Décommentez si l'écho local est désactivé sur le Minitel
                    user_input += decoded
            except (UnicodeDecodeError, ValueError):
                pass
    def ask_ollama(self, prompt):
        """Envoie la requête à Ollama et affiche la réponse en streaming"""
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "mistral",
            "prompt": prompt
        }

        self.send(self.WHITE_TEXT)
        self.send("\n\rMINITEL > ")

        try:
            # On utilise stream=True pour recevoir la réponse petit à petit
            with requests.post(url, json=payload, stream=True, timeout=10) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        # Décodage du JSON reçu
                        chunk = json.loads(line.decode('utf-8'))
                        content = chunk.get("response", "")

                        # On affiche le morceau de texte sur le Minitel
                        if content:
                            self.send(content)

                        # Si Ollama a fini
                        if chunk.get("done", False):
                            break

        except requests.exceptions.RequestException as e:
            self.send("\n\rErreur : Impossible de joindre Ollama.\n\r")
            print(f"Erreur API : {e}")

    def wait_for_minitel(self):
        """Boucle d'attente jusqu'à ce que le Minitel envoie un signal d'allumage"""
        print("En attente de l'allumage du Minitel...")
        self.ser.reset_input_buffer()
        while True:
            # On cherche le signal d'allumage typique (0x00 ou n'importe quel signal)
            char = self.ser.read(1)
            if char:
                print(f"Signal reçu ({char.hex()}), Minitel prêt !")
                time.sleep(3)  # Laisse le temps au Minitel d'être stable
                return True
    def run(self):
        try:
            self.wait_for_minitel()
            time.sleep(3)
            #Affichage page simulation connextion
            USERNAME = self.connexion_simulation()
            #Initialisation interface chat
            self.setup_ui()
            while True:
                self.send(self.GREEN_TEXT)
                self.send(f"{USERNAME} > ")
                question = self.get_input()

                if question.strip().lower() == "exit":
                    self.send("\n\rAu revoir !")
                    time.sleep(0.5)
                    self.send(self.CLEAR_SCREEN)
                    self.send(self.CURSOR_HOME)
                    self.send(self.WHITE_TEXT)
                    self.send("\n\rCerveau non disponible, je suis juste un minitel...\n\r")
                    print("Déconnexion...")
                    break

                if question.strip().lower() == "clear":
                    self.setup_ui()
                    continue

                # Gestion des réponses
                if(question=="SITUATION"):
                    response=f"Mais, vous savez, moi je ne crois pas qu’il y ait de bonne ou de mauvaise situation. Moi, si je devais résumer ma vie aujourd’hui avec vous, je dirais que c’est d’abord des rencontres, des gens qui m’ont tendu la main, peut-être à un moment où je ne pouvais pas, où j’étais seul chez moi. Et c’est assez curieux de se dire que les hasards, les rencontres forgent une destinée… Parce que quand on a le goût de la chose, quand on a le goût de la chose bien faite, le beau geste, parfois on ne trouve pas l’interlocuteur en face, je dirais, le miroir qui vous aide à avancer. Alors ce n’est pas mon cas, comme je le disais là, puisque moi au contraire, j’ai pu ; et je dis merci à la vie, je lui dis merci, je chante la vie, je danse la vie… Je ne suis qu’amour ! Et finalement, quand beaucoup de gens aujourd’hui me disent : STOP pitié"
                    self.send(self.WHITE_TEXT)
                    self.send("\n\rMINITEL > ")
                    self.send(response)
                else:
                    # Appel à Ollama en mode streaming
                    self.ask_ollama(question)

                self.send("\n\r\n\r")

        except KeyboardInterrupt:
            self.send("\n\rAu revoir !")
            time.sleep(0.5)
            self.send(self.CLEAR_SCREEN)
            self.send(self.CURSOR_HOME)
            self.send(self.WHITE_TEXT)
            self.send("\n\rCerveau non disponible, je suis juste un minitel...\n\r")
            print("Déconnexion...")

        except MinitelResetException:#gestion de l'extinction ou deconnexion
            print("Redémarrage du processus à zéro...")
            time.sleep(0.5)
            # On boucle et on revient à wait_for_minitel()
            self.run()

        finally:
            self.ser.close()

if __name__ == "__main__":
    SERIAL_PORT = scan_serial_port()
    bot = MinitelChatbot()
    bot.run()