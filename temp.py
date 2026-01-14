def ask_ollama(self, prompt, username):
    url = "http://localhost:11434/api/generate"
    payload = {"model": "mistral", "prompt": prompt}

    # On affiche le préfixe de réponse
    prefix = "MINITEL > "
    self.send(self.WHITE_TEXT)
    self.send("\n\r", prefix)

    # Mise à jour précise après le préfixe
    self.current_line += 1
    self.current_col = len(prefix)

    try:
        with requests.post(url, json=payload, stream=True, timeout=10) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    content = self.filter_text(chunk.get("response", ""))

                    if content:
                        # send_with_count va maintenant déclencher wait_for_suite
                        # au bon moment car current_line est juste !
                        self.send_with_count(content, username)

                    if chunk.get("done", False):
                        self.beep()
                        break
    except Exception as e:
        self.send(f"\n\rErreur : {e}")