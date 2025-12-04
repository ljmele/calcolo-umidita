import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Configurazione pagina
st.set_page_config(page_title="Calcolo Condensa", page_icon="💧")

st.title("💧 Calcolo Condensa")
st.write("Verifica se avrai muffa o condensa in casa.")

# 1. INPUT
col1, col2 = st.columns(2)
with col1:
    t_esterna = st.number_input("Temp. Esterna (°C)", value=10.0, step=0.5)
    rh_esterna = st.number_input("Umidità Esterna (%)", value=80.0, step=1.0)
with col2:
    t_interna = st.number_input("Temp. Casa (°C)", value=22.0, step=0.5)

# 2. CALCOLI
b, c = 17.67, 243.5
def get_pressione(temp):
    return 611.2 * np.exp((b * temp) / (c + temp))

def get_dew_point(temp, rh):
    gamma = np.log(rh / 100.0) + (b * temp) / (c + temp)
    return (c * gamma) / (b - gamma)

p_vapore = get_pressione(t_esterna) * (rh_esterna / 100.0)
psat_int = get_pressione(t_interna)
rh_finale = (p_vapore / psat_int) * 100
dew_point = get_dew_point(t_esterna, rh_esterna)

# 3. RISULTATI
st.divider()
kpi1, kpi2 = st.columns(2)
kpi1.metric("Umidità in Casa", f"{rh_finale:.1f}%")
kpi2.metric("Punto di Rugiada", f"{dew_point:.1f}°C")

if dew_point > 15:
    st.error(f"⚠️ **PERICOLO MUFFA!** Le pareti fredde sotto i {dew_point:.1f}°C si bagneranno.")
elif rh_finale < 30:
    st.warning("⚠️ **ARIA TROPPO SECCA!** Potrebbe irritare la gola.")
else:
    st.success("✅ **SITUAZIONE OK!** Parametri ideali.")

# 4. GRAFICO
fig, ax = plt.subplots()
temp_range = np.linspace(dew_point - 5, max(30, t_interna + 5), 100)

# Curve di sfondo
for rh in [20, 40, 60, 80, 100]:
    p_curve = get_pressione(temp_range) * (rh / 100.0)
    ax.plot(temp_range, p_curve, color='gray', alpha=0.2)
    ax.text(temp_range[-1], p_curve[-1], f'{rh}%', fontsize=8, color='gray')

# Processo
ax.plot([t_esterna, t_interna], [p_vapore, p_vapore], color='red', label='Riscaldamento', linewidth=2)
ax.scatter([t_esterna], [p_vapore], color='blue', zorder=5) # Start
ax.scatter([t_interna], [p_vapore], color='orange', zorder=5) # End

# Condensa
ax.axvline(x=dew_point, color='blue', linestyle='--', alpha=0.5, label='Punto Rugiada')
ax.grid(True, alpha=0.3)
ax.set_title("Diagramma Psicrometrico")
ax.set_xlabel("Temperatura (°C)")
ax.set_ylabel("Pressione Vapore (Pa)")
st.pyplot(fig)
