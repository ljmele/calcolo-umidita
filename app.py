import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Configurazione pagina
st.set_page_config(page_title="Meteo Casa & Acari", page_icon="🏠")

st.title("🏠 Meteo Casa & Acari")
st.write("Calcolatore per condensa e comfort allergico.")

# --- 1. INPUT DATI ---
col1, col2 = st.columns(2)
with col1:
    t_esterna = st.number_input("Temp. Esterna (°C)", value=10.0, step=0.5)
    rh_esterna = st.number_input("Umidità Esterna (%)", value=80.0, step=1.0)
with col2:
    t_interna = st.number_input("Temp. Casa (°C)", value=20.0, step=0.5)

# --- 2. CALCOLI FISICI ---
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

# --- 3. RESPONSORI ---
st.divider()

# -- SEZIONE ACARI (Nuova) --
st.subheader("🕷️ Rischio Acari")
if rh_finale < 45:
    st.success(f"✅ **OTTIMO (UR {rh_finale:.1f}%):** L'aria è troppo secca per gli acari. Muoiono o non si riproducono.")
elif rh_finale <= 50:
    st.warning(f"⚠️ **ATTENZIONE (UR {rh_finale:.1f}%):** Sei nella zona limite. Cerca di non farla alzare.")
else:
    st.error(f"⛔ **PERICOLO (UR {rh_finale:.1f}%):** Umidità troppo alta! Gli acari proliferano. Accendi il deumidificatore.")

# -- SEZIONE CONDENSA --
st.subheader("💧 Rischio Condensa")
col_a, col_b = st.columns(2)
col_a.metric("Punto di Rugiada", f"{dew_point:.1f}°C")

if dew_point > 15:
    st.error(f"I vetri si bagneranno se scendono sotto i {dew_point:.1f}°C.")
else:
    st.info(f"Condensa solo su superfici sotto i {dew_point:.1f}°C.")

# --- 4. GRAFICO ---
fig, ax = plt.subplots(figsize=(6, 4))
# Disegno un po' di margine attorno ai dati
t_min_plot = min(dew_point, t_esterna) - 5
t_max_plot = max(30, t_interna) + 5
temp_range = np.linspace(t_min_plot, t_max_plot, 100)

# Zone di sfondo per gli acari
# Zona Verde (Sotto 45%)
p_45 = get_pressione(temp_range) * 0.45
ax.fill_between(temp_range, 0, p_45, color='green', alpha=0.1, label='Zona No Acari (<45%)')

# Curve umidità classiche
for rh in [50, 80, 100]:
    p_curve = get_pressione(temp_range) * (rh / 100.0)
    ax.plot(temp_range, p_curve, color='gray', linestyle='--', alpha=0.3)
    ax.text(temp_range[-1], p_curve[-1], f'{rh}%', fontsize=8, color='gray')

# Processo (Freccia Rossa)
ax.annotate("", xy=(t_interna, p_vapore_ext), xytext=(t_esterna, p_vapore_ext),
            arrowprops=dict(arrowstyle="->", color="red", lw=2))
ax.scatter([t_esterna], [p_vapore_ext], color='blue', label='Esterno')
ax.scatter([t_interna], [p_vapore_ext], color='red', label='Interno')

# Punto di rugiada
ax.scatter([dew_point], [p_vapore_ext], color='cyan', edgecolors='blue', zorder=5)

ax.set_title("Grafico Psicrometrico (Zona Verde = No Acari)")
ax.set_xlabel("Temperatura (°C)")
ax.set_ylabel("Pressione Vapore")
ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', fontsize='small')

st.pyplot(fig)
