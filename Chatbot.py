import serial
import time
import sys
import serial.tools.list_ports

BAUD_RATE = 1200  # Vitesse standard Minitel mode videotexte


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

    def send(self, data):
        """Envoie des données au Minitel en s'assurant qu'elles sont au format bytes"""
        if isinstance(data, str):
            data = data.encode('ascii', errors='replace')

        self.ser.write(data)

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
        """Lit les caractères et gère les séquences spécifiques de votre Minitel"""
        user_input = ""
        while True:
            char = self.ser.read(1)
            if not char:
                continue

            # DEBUG réception sérial
            # print(f"DEBUG: Reçu {char.hex()} ({char})")

            # Détection du préfixe de la touche envoi du minitel 1B (0x13)
            if char == b'\x13':
                next_char = self.ser.read(1)
                if next_char == b'A':
                    self.send("\n\r")
                    return user_input
                continue

            # Gestion de la touche "Correction" (souvent 0x08 ou 0x7F)
            #TO DO
            if char == b'\x08' or char == b'\x7f':
                if len(user_input) > 0:
                    user_input = user_input[:-1]
                    self.send(b'\x08 \x08')
                continue

            # Echo local et stockage du texte
            try:
                # On n'accepte que les caractères imprimables (espace et au-delà)
                if ord(char) >= 32:
                    decoded = char.decode('ascii')
                    #self.send(char)  #Echo local géré par le minitel
                    user_input += decoded
            except UnicodeDecodeError:
                pass
    def run(self):
        try:
            self.setup_ui()
            while True:
                self.send(self.GREEN_TEXT)
                self.send("MINITEL > ")
                question = self.get_input()

                if question.strip().lower() == "exit":
                    break

                # Gestion des réponses
                if(question=="SITUATION"):
                    response=f"Mais, vous savez, moi je ne crois pas qu’il y ait de bonne ou de mauvaise situation. Moi, si je devais résumer ma vie aujourd’hui avec vous, je dirais que c’est d’abord des rencontres, des gens qui m’ont tendu la main, peut-être à un moment où je ne pouvais pas, où j’étais seul chez moi. Et c’est assez curieux de se dire que les hasards, les rencontres forgent une destinée… Parce que quand on a le goût de la chose, quand on a le goût de la chose bien faite, le beau geste, parfois on ne trouve pas l’interlocuteur en face, je dirais, le miroir qui vous aide à avancer. Alors ce n’est pas mon cas, comme je le disais là, puisque moi au contraire, j’ai pu ; et je dis merci à la vie, je lui dis merci, je chante la vie, je danse la vie… Je ne suis qu’amour ! Et finalement, quand beaucoup de gens aujourd’hui me disent : STOP pitié"
                else:
                    response = f"Vous avez dit : {question}. Pour le moment je suis toujours un minitel qui ne sait pas répondre aux questions."


                self.send(self.WHITE_TEXT )
                self.send("\n\rIA> : ")
                self.send(response)
                self.send("\n\r\n\r")

        except KeyboardInterrupt:
            print("Déconnexion...")
        finally:
            self.ser.close()


if __name__ == "__main__":
    SERIAL_PORT = scan_serial_port()
    bot = MinitelChatbot()
    bot.run()