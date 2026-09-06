class TextParser:
    @staticmethod
    def extract_text(file_bytes: bytes, encoding: str = "utf-8") -> str:
        """Decodifica archivos de texto plano o Markdown con manejo de encodings comunes."""
        for enc in [encoding, "utf-8", "latin-1", "cp1252"]:
            try:
                return file_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace")
