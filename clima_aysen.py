import os
import requests
import json
from google import genai
from dotenv import load_dotenv

# Cargamos el entorno y configuramos el cliente de IA
load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def obtener_datos_completos():
    print("⏳ 1. Descargando clima actual de DGAC (Teniente Vidal)...")
    url_dgac = "https://climatologia.meteochile.gob.cl/application/diariob/visorDeDatosEma/450004"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        html_dgac = requests.get(url_dgac, headers=headers, timeout=15).text
        print("✅ Datos DGAC obtenidos.")
    except Exception as e:
        html_dgac = "Error al obtener DGAC"
        print(f"❌ Error DGAC: {e}")

    print("⏳ 2. Descargando pronóstico y viento de Open-Meteo...")
    # Coordenadas exactas del aeródromo para el pronóstico horario
    url_om = "https://api.open-meteo.com/v1/forecast?latitude=-45.5752&longitude=-72.1024&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m&timezone=America%2FSantiago&forecast_days=1"
    
    try:
        json_om = requests.get(url_om, timeout=10).text
        print("✅ Pronóstico Open-Meteo obtenido.")
    except Exception as e:
        json_om = "Error al obtener Open-Meteo"
        print(f"❌ Error Open-Meteo: {e}")

    return html_dgac, json_om

def analizar_clima_con_ia(html_dgac, json_om):
    print("🧠 3. Gemini 2.5 Flash está fusionando y estructurando los datos...")
    
    prompt = f"""
    Eres el procesador de datos de un panel de tinta electrónica familiar.
    
    Fuente 1 (Clima actual local): HTML de la estación DGAC
    {html_dgac}
    
    Fuente 2 (Pronóstico del día): JSON de Open-Meteo
    {json_om}
    
    Analiza ambas fuentes y devuelve estrictamente un archivo JSON con esta estructura exacta:
    {{
        "mensaje": "Mensaje cálido (máx 3 líneas) para la familia sobre cómo prepararse para caminar 500 metros al colegio.",
        "escenario_imagen": "Elige una: frio_extremo | lluvia | despejado_bici | calor_playa",
        "viento_actual": {{
            "velocidad": "XX km/h",
            "direccion_texto": "N, NW, S, SE, etc.",
            "angulo": (Número entero entre 0 y 360)
        }},
        "pronostico_tarde": {{
            "12:00": {{"icono": "sol|nubes|lluvia|nieve", "temp": "X°C"}},
            "16:00": {{"icono": "sol|nubes|lluvia|nieve", "temp": "X°C"}},
            "20:00": {{"icono": "sol|nubes|lluvia|nieve", "temp": "X°C"}}
        }}
    }}
    
    Regla: Para el viento, extrae la dirección y velocidad del HTML de DGAC si está disponible. Si no, usa la hora actual del JSON de Open-Meteo.
    """

    try:
        respuesta = cliente.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )
        
        resultado_json = json.loads(respuesta.text)
        print("✅ Análisis JSON generado con éxito.")
        return resultado_json

    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        # JSON de respaldo en caso de fallo crítico de internet
        return {
            "mensaje": "Revisar por la ventana, problemas de conexión.",
            "escenario_imagen": "frio_extremo",
            "viento_actual": {"velocidad": "0 km/h", "direccion_texto": "N", "angulo": 0},
            "pronostico_tarde": {"12:00": {"icono": "nubes", "temp": "--"}, "16:00": {"icono": "nubes", "temp": "--"}, "20:00": {"icono": "nubes", "temp": "--"}}
        }

def exportar_resultado(resultado):
    nombre_archivo = "clima_exportado.json"
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, indent=4, ensure_ascii=False)
        
    print("\n--- RESUMEN FINAL ---")
    print(f"Mensaje : {resultado.get('mensaje', '')}")
    print(f"Imagen  : {resultado.get('escenario_imagen', '')}.bmp")
    print(f"Viento  : {resultado.get('viento_actual', {}).get('direccion_texto', '')} a {resultado.get('viento_actual', {}).get('velocidad', '')} (Ángulo: {resultado.get('viento_actual', {}).get('angulo', '')}°)")
    print(f"12:00   : {resultado.get('pronostico_tarde', {}).get('12:00', {}).get('temp', '')} ({resultado.get('pronostico_tarde', {}).get('12:00', {}).get('icono', '')})")
    print(f"16:00   : {resultado.get('pronostico_tarde', {}).get('16:00', {}).get('temp', '')} ({resultado.get('pronostico_tarde', {}).get('16:00', {}).get('icono', '')})")
    print("---------------------\n")

if __name__ == "__main__":
    html_crudo, json_crudo = obtener_datos_completos()
    analisis_final = analizar_clima_con_ia(html_crudo, json_crudo)
    exportar_resultado(analisis_final)