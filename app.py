import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests

# Configurazione pagina
st.set_page_config(page_title="Meteo Casa & Acari", page_icon="🏠")

# --- FUNZIONE PER SCARICARE I DATI ---
def get_meteo(citta):
    try:
        # 1. Trova le coordinate della città (Geocoding)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={citta}&count=1&language=it&format=json"
        geo_res = requests.get(geo_url).json()
        
        if not geo_res.get("results"):
            return None, None, "Città non trovata!"
            
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        nome_trovato = geo_res["results"][0]["name"]
        
        # 2. Scarica il meteo attuale
        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        meteo_res = requests.get(meteo_url).json()
        
        temp = meteo_res["current"]["temperature_2m"]
        hum = meteo_res["current"]["relative_humidity_2m"]
        
        return temp, hum, f"Dati scaricati per {nome_trovato}"
        
    except Exception as e:
        return None, None, f"Errore di connessione: {e}"

# --- INTERFACCIA UTENTE ---
st.title("🏠 Meteo Casa & Acari")

# Inizializza le variabili se non esistono (Default iniziale)
if 't_ext' not in st.session_state: st.session_state.t_ext = 10.0
if 'rh_ext' not in st.session_state: st.session_state.rh_ext = 80.0

# Sezione Ricerca Città
st.subheader("🌍 Dove ti trovi?")
col_citta, col_btn = st.columns([3, 1])
with col_citta:
    citta_input = st.text_input("Scrivi la tua città", value="Udine")
with col_btn:
    st.write("") # Spaziatura estetica
    st.write("") 
    if st.button("🔄 Aggiorna Meteo"):
        t_new, h_new, msg = get_meteo(citta_input)
        if t_new is not None:
            st.session_state.t_ext = t_new
            st.session_state.rh_ext = float(h_new) # Assicuriamoci sia float
            st.success(msg)
        else:
            st.error(msg)

st.divider()

# --- INPUT DATI (Modificabili) ---
st.write("Puoi modificare manualmente i dati qui sotto se necessario:")
col1, col2 = st.columns(2)
with col1:
    # Usiamo key=... per collegarli allo session_state aggiornato dal bottone
    t_esterna = st.number_input("Temp. Esterna (°C)", key="t_ext", step=0.5)
    rh_esterna = st.number_input("Umidità Esterna (%)", key="rh_ext", step=1.0)
with col2:
    t_interna = st.number_input("Temp. Casa Target (°C)", value=20.0, step=0.5)

# --- CALCOLI FISICI ---
b, c = 17.67, 243.5
def get_pressione(temp):
    return 611.2 * np.exp((b * temp) / (c + temp))

def get_dew_point(temp, rh):
    gamma = np.log(rh / 100.0) + (b * temp) / (c + temp)
    return (c * gamma) / (b - gamma)

p_vapore_ext = get_pressione(t_esterna) * (rh_esterna / 100.0)
psat_int = get_pressione(t_interna)
rh_finale = (p_vapore_ext / psat_int) * 100
dew_point = get_dew_point(t_esterna, rh_esterna)

# --- RISULTATI E AVVISI ---
st.divider()
st.subheader("📊 Analisi")

col_kpi1, col_kpi2 = st.columns(2)
col_kpi1.metric("Umidità Prevista in Casa", f"{rh_finale:.1f}%")
col_kpi2.metric("Punto di Rugiada", f"{dew_point:.1f}°C")

# Avviso Acari
if rh_finale < 45:
    st.success(f"🕷️ **ACARI OK:** Umidità al {rh_finale:.1f}%. Ottimo per allergici.")
elif rh_finale <= 50:
    st.warning(f"🕷️ **ACARI ATTENZIONE:** Umidità al {rh_finale:.1f}%. Zona limite.")
else:
    st.error(f"🕷️ **ACARI PERICOLO:** Umidità al {rh_finale:.1f}%. Accendi il deumidificatore!")

# Avviso Condensa
if dew_point > 15:
    st.error(f"💧 **CONDENSA:** Rischio molto alto. Vetri e muri freddi si bagneranno.")
elif dew_point > 10:
    st.warning(f"💧 **CONDENSA:** Possibile su vetri singoli o ponti termici (<{dew_point:.1f}°C).")
else:
    st.info(f"💧 **CONDENSA:** Rischio basso (solo se superfici <{dew_point:.1f}°C).")

# --- GRAFICO ---
fig, ax = plt.subplots(figsize=(6, 4))
t_min_plot = min(dew_point, t_esterna) - 5
t_max_plot = max(30, t_interna) + 5
temp_range = np.linspace(t_min_plot, t_max_plot, 100)

# Zona verde Acari
p_45 = get_pressione(temp_range) * 0.45
ax.fill_between(temp_range, 0, p_45, color='green', alpha=0.1, label='Zona sicura Acari')

# Curve
for rh in [50, 80, 100]:
    p_curve = get_pressione(temp_range) * (rh / 100.0)
    ax.plot(temp_range, p_curve, color='gray', linestyle='--', alpha=0.3)
    ax.text(temp_range[-1], p_curve[-1], f'{rh}%', fontsize=8, color='gray')

# Processo
ax.plot([t_esterna, t_interna], [p_vapore_ext, p_vapore_ext], color='red', lw=2)
ax.scatter([t_esterna], [p_vapore_ext], color='blue')
ax.scatter([t_interna], [p_vapore_ext], color='red')
ax.scatter([dew_point], [p_vapore_ext], color='cyan', edgecolors='blue', zorder=5)

ax.set_title(f"Situazione da {t_esterna}°C a {t_interna}°C")
ax.set_xlabel("Temperatura (°C)")
ax.set_ylabel("Pressione Vapore")
ax.grid(True, alpha=0.3)
st.pyplot(fig)
