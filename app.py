import streamlit as st
import googlemaps
import folium
from streamlit_folium import st_folium
import polyline
import pandas as pd
from urllib.parse import quote

# -----------------------------------------------------------------------------
# 1. Configuración de la App y API Key
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Gestor de Rutas de Obras", layout="wide")
st.title("📍 Planificador de Rutas e Inspección de Obras")

# Puedes colocar tu API Key directamente o ingresarla desde la barra lateral
api_key = st.sidebar.text_input("Google Maps API Key", type="password")

if not api_key:
    st.info("👈 Introduce tu API Key de Google Maps en el panel lateral para iniciar.")
    st.stop()

gmaps = googlemaps.Client(key=api_key)

# -----------------------------------------------------------------------------
# 2. Base de Datos Ejemplo (Simulada o desde CSV/Excel)
# -----------------------------------------------------------------------------
# En producción puedes usar: df_obras = pd.read_excel("obras.xlsx")
data_obras = [
    {"ID": "OBRA-001", "Nombre": "Oficina Central / Salida", "Latitud": 21.0165, "Longitud": -101.2520},
    {"ID": "OBRA-002", "Nombre": "Rehabilitación de Pimentel / La Postura", "Latitud": 21.0280, "Longitud": -101.2650},
    {"ID": "OBRA-003", "Nombre": "Construcción Pozo Profundo - Ficha A", "Latitud": 20.9850, "Longitud": -101.2900},
    {"ID": "OBRA-004", "Nombre": "Camino Rural Ejidal San Nicolás", "Latitud": 21.1200, "Longitud": -101.6800},
]
df_obras = pd.DataFrame(data_obras)

# -----------------------------------------------------------------------------
# 3. Interfaz de Selección
# -----------------------------------------------------------------------------
col_origen, col_destino = st.columns(2)

with col_origen:
    origen_nombre = st.selectbox("Selecciona Punto de Origen:", df_obras["Nombre"])
    origen_row = df_obras[df_obras["Nombre"] == origen_nombre].iloc[0]
    origen_coords = (origen_row["Latitud"], origen_row["Longitud"])

with col_destino:
    destino_nombre = st.selectbox("Selecciona Obra Destino:", df_obras["Nombre"], index=1)
    destino_row = df_obras[df_obras["Nombre"] == destino_nombre].iloc[0]
    destino_coords = (destino_row["Latitud"], destino_row["Longitud"])

# -----------------------------------------------------------------------------
# 4. Cálculo de Ruta con Google Maps API
# -----------------------------------------------------------------------------
if st.button("🚀 Calcular Ruta"):
    if origen_nombre == destino_nombre:
        st.warning("El origen y el destino deben ser puntos distintos.")
    else:
        try:
            # Consulta a Google Directions API (Modo Auto / Driving)
            directions_result = gmaps.directions(
                origin=origen_coords,
                destination=destino_coords,
                mode="driving",
                departure_time="now"  # Considera tráfico en tiempo real
            )

            if directions_result:
                leg = directions_result[0]['legs'][0]
                distancia = leg['distance']['text']
                tiempo = leg['duration']['text']
                tiempo_trafico = leg.get('duration_in_traffic', {}).get('text', tiempo)

                # Muestra Métricas
                c1, c2, c3 = st.columns(3)
                c1.metric("Distancia por Carretera", distancia)
                c2.metric("Tiempo Estimado", tiempo)
                c3.metric("Tiempo con Tráfico", tiempo_trafico)

                # Generar Enlace URL Estándar de Google Maps para Celular
                url_gmaps = (
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&origin={origen_coords[0]},{origen_coords[1]}"
                    f"&destination={destino_coords[0]},{destino_coords[1]}"
                    f"&travelmode=driving"
                )

                st.markdown(f"📲 **[Abrir esta ruta directamente en Google Maps]({url_gmaps})**")

                # -------------------------------------------------------------
                # 5. Renderizado en Mapa Interactivo (Folium)
                # -------------------------------------------------------------
                # Decodificar la polínea que devuelve Google
                encoded_polyline = directions_result[0]['overview_polyline']['points']
                route_points = polyline.decode(encoded_polyline)

                # Crear mapa centrado en el punto medio
                centro_lat = (origen_coords[0] + destino_coords[0]) / 2
                centro_lon = (origen_coords[1] + destino_coords[1]) / 2
                m = folium.Map(location=[centro_lat, centro_lon], zoom_start=12)

                # Marcadores de Origen y Destino
                folium.Marker(
                    origen_coords,
                    popup=f"Origen: {origen_nombre}",
                    icon=folium.Icon(color="green", icon="play")
                ).add_to(m)

                folium.Marker(
                    destino_coords,
                    popup=f"Destino: {destino_nombre}",
                    icon=folium.Icon(color="red", icon="flag")
                ).add_to(m)

                # Dibujar Trazo de Ruta
                folium.PolyLine(
                    locations=route_points,
                    color="#1A73E8",
                    weight=5,
                    opacity=0.8
                ).add_to(m)

                # Mostrar Mapa en Streamlit
                st_folium(m, width=900, height=500)

            else:
                st.error("No se encontró una ruta terrestre válida entre ambos puntos.")

        except Exception as e:
            st.error(f"Error al consultar la API de Google Maps: {e}")
