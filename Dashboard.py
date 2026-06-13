# dashboard_reunion_realtime.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Météo La Réunion - Données Réelles",
    page_icon="🌴",
    layout="wide"
)

# ==================== DONNÉES DES 24 COMMUNES ====================
COMMUNES_REUNION = [
    {"nom": "Saint-Denis", "lat": -20.8789, "lon": 55.4481, "altitude": 20, "zone": "Nord"},
    {"nom": "Saint-Paul", "lat": -21.0096, "lon": 55.2696, "altitude": 5, "zone": "Ouest"},
    {"nom": "Saint-Pierre", "lat": -21.3419, "lon": 55.4778, "altitude": 10, "zone": "Sud"},
    {"nom": "Le Tampon", "lat": -21.2808, "lon": 55.5192, "altitude": 750, "zone": "Intérieur"},
    {"nom": "Saint-André", "lat": -20.9600, "lon": 55.6500, "altitude": 15, "zone": "Est"},
    {"nom": "Saint-Louis", "lat": -21.2861, "lon": 55.4097, "altitude": 30, "zone": "Sud"},
    {"nom": "Le Port", "lat": -20.9397, "lon": 55.2875, "altitude": 5, "zone": "Ouest"},
    {"nom": "Saint-Benoît", "lat": -21.0339, "lon": 55.7125, "altitude": 10, "zone": "Est"},
    {"nom": "Sainte-Marie", "lat": -20.8969, "lon": 55.5500, "altitude": 10, "zone": "Nord"},
    {"nom": "Sainte-Suzanne", "lat": -20.9056, "lon": 55.6075, "altitude": 15, "zone": "Nord"},
    {"nom": "La Possession", "lat": -20.9264, "lon": 55.3358, "altitude": 10, "zone": "Nord"},
    {"nom": "Les Trois-Bassins", "lat": -21.1056, "lon": 55.2964, "altitude": 100, "zone": "Ouest"},
    {"nom": "Saint-Leu", "lat": -21.1706, "lon": 55.2875, "altitude": 50, "zone": "Ouest"},
    {"nom": "L'Étang-Salé", "lat": -21.2658, "lon": 55.3653, "altitude": 10, "zone": "Sud"},
    {"nom": "Les Avirons", "lat": -21.2425, "lon": 55.3394, "altitude": 50, "zone": "Sud"},
    {"nom": "Petite-Île", "lat": -21.3528, "lon": 55.5650, "altitude": 30, "zone": "Sud"},
    {"nom": "Saint-Joseph", "lat": -21.3786, "lon": 55.6200, "altitude": 20, "zone": "Sud"},
    {"nom": "Saint-Philippe", "lat": -21.3608, "lon": 55.7681, "altitude": 10, "zone": "Sud"},
    {"nom": "Bras-Panon", "lat": -20.9950, "lon": 55.6750, "altitude": 20, "zone": "Est"},
    {"nom": "Sainte-Rose", "lat": -21.1267, "lon": 55.7914, "altitude": 20, "zone": "Est"},
    {"nom": "La Plaine-des-Palmistes", "lat": -21.1336, "lon": 55.6256, "altitude": 1050, "zone": "Est"},
    {"nom": "Cilaos", "lat": -21.1358, "lon": 55.4711, "altitude": 1200, "zone": "Intérieur"},
    {"nom": "Salazie", "lat": -21.0278, "lon": 55.5389, "altitude": 450, "zone": "Intérieur"},
    {"nom": "L'Entre-Deux", "lat": -21.2419, "lon": 55.4681, "altitude": 380, "zone": "Intérieur"}
]

ZONES = {
    "Nord": ["Saint-Denis", "Sainte-Marie", "Sainte-Suzanne", "La Possession"],
    "Ouest": ["Saint-Paul", "Le Port", "Les Trois-Bassins", "Saint-Leu"],
    "Sud": ["Saint-Pierre", "Saint-Louis", "L'Étang-Salé", "Les Avirons", "Petite-Île", "Saint-Joseph", "Saint-Philippe"],
    "Est": ["Saint-André", "Saint-Benoît", "Bras-Panon", "Sainte-Rose", "La Plaine-des-Palmistes"],
    "Intérieur": ["Le Tampon", "Cilaos", "Salazie", "L'Entre-Deux"]
}

class MeteoOpenMeteo:
    """Récupère les données météo via Open-Meteo - GRATUIT, SANS INSCRIPTION"""
    
    def __init__(self):
        self.last_update = None
        self.cache = {}
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather_for_commune(self, commune, lat, lon):
        """Appelle Open-Meteo pour une commune - sans clé API !"""
        
        # Cache 10 minutes
        cache_key = commune
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).seconds < 600:
                return cached_data
        
        # Paramètres de la requête Open-Meteo
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,pressure_msl,uv_index",
            "timezone": "Indian/Reunion",
            "forecast_days": 1
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                
                weather_data = {
                    "temperature": current.get("temperature_2m", 0),
                    "feels_like": current.get("apparent_temperature", 0),
                    "humidity": current.get("relative_humidity_2m", 0),
                    "wind_speed": current.get("wind_speed_10m", 0),
                    "wind_gusts": current.get("wind_gusts_10m", 0),
                    "wind_direction": current.get("wind_direction_10m", 0),
                    "precipitation": current.get("precipitation", 0),
                    "pressure": current.get("pressure_msl", 0),
                    "cloud_cover": current.get("cloud_cover", 0),
                    "uv_index": current.get("uv_index", 0),
                    "weather_code": self.get_weather_code(current)
                }
                
                # Ajout de la condition texte
                weather_data["condition"] = self.get_weather_description(weather_data["weather_code"])
                weather_data["icon"] = self.get_weather_icon(weather_data["weather_code"])
                
                self.cache[cache_key] = (weather_data, datetime.now())
                return weather_data
                
            else:
                return self.get_fallback_data(commune)
                
        except Exception as e:
            st.warning(f"Erreur pour {commune}: {str(e)[:50]}...")
            return self.get_fallback_data(commune)
    
    def get_weather_code(self, current):
        """Détermine le code météo WMO"""
        # Approximation basée sur les données disponibles
        if current.get("precipitation", 0) > 5:
            return 61  # Pluie
        elif current.get("precipitation", 0) > 0:
            return 51  # Bruine
        elif current.get("cloud_cover", 0) > 80:
            return 3   # Couvert
        elif current.get("cloud_cover", 0) > 40:
            return 2   # Partiellement nuageux
        else:
            return 0   # Clair
    
    def get_weather_description(self, code):
        """Traduit le code WMO en description [citation:8]"""
        descriptions = {
            0: "Ciel dégagé",
            1: "Principalement dégagé",
            2: "Partiellement nuageux",
            3: "Couvert",
            45: "Brouillard",
            51: "Bruine légère",
            53: "Bruine modérée",
            55: "Bruine dense",
            61: "Pluie légère",
            63: "Pluie modérée",
            65: "Pluie forte",
            80: "Averses légères",
            81: "Averses modérées",
            82: "Averses violentes",
            95: "Orage"
        }
        return descriptions.get(code, "Variable")
    
    def get_weather_icon(self, code):
        """Retourne un emoji selon le code météo"""
        if code in [0, 1]:
            return "☀️"
        elif code in [2]:
            return "⛅"
        elif code in [3, 45]:
            return "☁️"
        elif code in [51, 53, 55]:
            return "🌦️"
        elif code in [61, 63, 65, 80, 81, 82]:
            return "🌧️"
        elif code == 95:
            return "⛈️"
        else:
            return "🌤️"
    
    def get_fallback_data(self, commune):
        """Données estimées si API indisponible"""
        commune_info = next((c for c in COMMUNES_REUNION if c["nom"] == commune), None)
        altitude = commune_info["altitude"] if commune_info else 100
        temp = 28 - (altitude / 1000 * 6.5)
        
        return {
            "temperature": round(temp, 1),
            "feels_like": round(temp - 1, 1),
            "humidity": 70,
            "wind_speed": 10,
            "wind_gusts": 15,
            "wind_direction": 90,
            "precipitation": 0,
            "pressure": 1013,
            "cloud_cover": 30,
            "uv_index": 8,
            "weather_code": 1,
            "condition": "Données estimées",
            "icon": "🌤️"
        }
    
    def get_all_weather(self):
        """Récupère la météo pour toutes les communes"""
        weather_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, commune in enumerate(COMMUNES_REUNION):
            status_text.text(f"Récupération météo : {commune['nom']}...")
            
            weather = self.get_weather_for_commune(
                commune["nom"], 
                commune["lat"], 
                commune["lon"]
            )
            
            weather_data.append({
                "commune": commune["nom"],
                "lat": commune["lat"],
                "lon": commune["lon"],
                "altitude": commune["altitude"],
                "zone": commune["zone"],
                **weather
            })
            
            progress_bar.progress((i + 1) / len(COMMUNES_REUNION))
            time.sleep(0.1)
        
        status_text.empty()
        progress_bar.empty()
        
        self.last_update = datetime.now()
        return pd.DataFrame(weather_data)


# ==================== CSS ====================
st.markdown("""
<style>
    .main-header { font-size: 2rem; text-align: center; margin-bottom: 1rem; color: #0066cc; }
    .commune-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem; border-radius: 12px; color: white; margin: 0.5rem 0;
    }
    .weather-temp { font-size: 1.8rem; font-weight: bold; }
    .weather-icon { font-size: 2rem; }
    .alert { background: #ff4444; padding: 0.3rem 0.6rem; border-radius: 20px; font-size: 0.7rem; }
    .last-update { text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)


def display_commune_card(row):
    """Affiche une carte météo pour une commune"""
    alert = ""
    if row["temperature"] > 32:
        alert = '<span class="alert">🌡️ Canicule</span>'
    elif row["wind_speed"] > 30:
        alert = '<span class="alert">💨 Vent fort</span>'
    elif row["precipitation"] > 5:
        alert = '<span class="alert">🌧️ Pluie</span>'
    
    st.markdown(f"""
    <div class="commune-card">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <b>{row['commune']}</b><br>
                <small>{row['zone']} • {row['altitude']}m</small>
            </div>
            <div class="weather-icon">{row['icon']}</div>
        </div>
        <div class="weather-temp">{row['temperature']:.1f}°C</div>
        <div>💨 {row['wind_speed']:.1f} km/h | 💧 {row['humidity']:.0f}%</div>
        <div>🌧️ {row['precipitation']:.1f} mm | ☀️ UV {row['uv_index']:.1f}</div>
        <div style="font-size:0.8rem">Ressenti {row['feels_like']:.1f}°C • {row['condition']}</div>
        {alert}
    </div>
    """, unsafe_allow_html=True)


def main():
    st.markdown('<h1 class="main-header">🌴 Météo La Réunion - Données Réelles 🌴</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center">📡 Données Open-Meteo (Météo-France) • Mise à jour automatique • 24 communes</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        auto_refresh = st.checkbox("🔄 Actualisation auto", value=True)
        refresh_rate = st.slider("Fréquence (minutes)", 1, 15, 5)
        
        st.markdown("---")
        st.markdown("## 🎯 Filtres")
        zone_filter = st.multiselect("Zones", list(ZONES.keys()), default=list(ZONES.keys()))
        
        st.markdown("---")
        st.markdown("## ℹ️ Source")
        st.info("Données météo fournies par [Open-Meteo](https://open-meteo.com) • Modèles Météo-France")
    
    # Chargement des données
    meteo = MeteoOpenMeteo()
    weather_df = meteo.get_all_weather()
    
    # Filtrage
    if zone_filter:
        communes_filtrees = []
        for zone in zone_filter:
            communes_filtrees.extend(ZONES[zone])
        weather_df = weather_df[weather_df["commune"].isin(communes_filtrees)]
    
    # Dernière mise à jour
    st.markdown(f'<p class="last-update">🕐 Dernière MAJ: {meteo.last_update.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🌡️ Température moyenne", f"{weather_df['temperature'].mean():.1f}°C",
                 f"Max: {weather_df['temperature'].max():.1f}°C")
    with col2:
        st.metric("💧 Humidité moyenne", f"{weather_df['humidity'].mean():.0f}%")
    with col3:
        st.metric("💨 Vent moyen", f"{weather_df['wind_speed'].mean():.1f} km/h")
    with col4:
        st.metric("🌧️ Pluie totale", f"{weather_df['precipitation'].sum():.1f} mm")
    
    # Carte
    st.markdown("### 🗺️ Carte des températures")
    fig = px.scatter_mapbox(
        weather_df, lat="lat", lon="lon", color="temperature",
        size="wind_speed", hover_name="commune",
        hover_data={"temperature": ":.1f°C", "humidity": ":.0f%", "condition": True},
        color_continuous_scale="RdYlBu_r", zoom=9,
        center={"lat": -21.1, "lon": 55.5}, height=450
    )
    fig.update_layout(mapbox_style="open-street-map", margin={"r":0, "t":0, "l":0, "b":0})
    st.plotly_chart(fig, use_container_width=True)
    
    # Grille des communes
    st.markdown("### 🏘️ Météo par commune")
    cols = st.columns(4)
    for idx, (_, row) in enumerate(weather_df.iterrows()):
        with cols[idx % 4]:
            display_commune_card(row)
    
    # Graphiques
    st.markdown("### 📊 Analyse par zone")
    col1, col2 = st.columns(2)
    
    with col1:
        zone_temp = weather_df.groupby("zone")["temperature"].agg(["mean", "min", "max"]).reset_index()
        fig_temp = px.bar(zone_temp, x="zone", y="mean", color="zone",
                         title="Température moyenne par zone",
                         labels={"mean": "Température (°C)", "zone": "Zone"})
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        fig_wind = px.box(weather_df, x="zone", y="wind_speed", color="zone",
                         title="Distribution des vents par zone")
        fig_wind.update_layout(showlegend=False)
        st.plotly_chart(fig_wind, use_container_width=True)
    
    # Tableau détaillé
    with st.expander("📋 Données détaillées des 24 communes"):
        display_df = weather_df[[
            "commune", "zone", "altitude", "temperature", "feels_like",
            "humidity", "wind_speed", "precipitation", "uv_index", "condition"
        ]].copy()
        display_df.columns = ["Commune", "Zone", "Altitude", "Température", "Ressenti",
                             "Humidité", "Vent", "Pluie", "UV", "Condition"]
        st.dataframe(display_df, use_container_width=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate * 60)
        st.rerun()


if __name__ == "__main__":
    main()
