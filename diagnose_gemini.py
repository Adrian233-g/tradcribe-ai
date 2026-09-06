import requests
import json

def diagnose_gemini_key(api_key: str):
    """Diagnóstico detallado de la clave de Gemini."""
    clean_key = api_key.strip().strip('"').strip("'")
    print(f"Longitud de la clave: {len(clean_key)} caracteres")
    print(f"Prefijo: {clean_key[:6]}... Sufijo: ...{clean_key[-4:]}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
    try:
        r = requests.get(url, timeout=15)
        print(f"Código HTTP de respuesta: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            models = [m['name'] for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            print(f"✓ Éxito: Se encontraron {len(models)} modelos con soporte de generateContent:")
            for m in models:
                print(f"  - {m}")
            return True, models
        else:
            print("❌ Error devuelto por Google:")
            print(r.text)
            return False, r.text
    except Exception as e:
        print(f"Excepción de conexión: {e}")
        return False, str(e)

if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    if key:
        diagnose_gemini_key(key)
    else:
        print("Por favor pasa la API Key como argumento para probar.")
