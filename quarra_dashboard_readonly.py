import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import timedelta

st.set_page_config(page_title="Quarra Dashboard", layout="centered")  # Ottimizzato per mobile
st.title("📊 Quarra Italia - Weekly Dashboard")

# Caricamento dati da file fisso incluso nel repository
data_file_path = "dati_quarra.xlsx"
xls = pd.ExcelFile(data_file_path)

# Lettura fogli
df_costi = pd.read_excel(xls, sheet_name="Costi")
df_produzione = pd.read_excel(xls, sheet_name="Produzione")
df_cassa = pd.read_excel(xls, sheet_name="Cassa")

# Pre-elaborazione: converte la colonna data
df_costi["Data"] = pd.to_datetime(df_costi["Data"])
df_produzione["Data"] = pd.to_datetime(df_produzione["Data"])
df_cassa["Data"] = pd.to_datetime(df_cassa["Data"])

# Raggruppamenti settimanali
def label_settimana(data):
    lunedi = data - timedelta(days=data.weekday())
    domenica = lunedi + timedelta(days=6)
    return f"{lunedi.day:02d}-{lunedi.strftime('%b')} → {domenica.day:02d}-{domenica.strftime('%b')}"

df_costi_weekly = df_costi.groupby(pd.Grouper(key="Data", freq="W-MON")).sum().reset_index()
df_costi_weekly["Settimana"] = df_costi_weekly["Data"].apply(label_settimana)

df_produzione_weekly = df_produzione.groupby(pd.Grouper(key="Data", freq="W-MON")).sum().reset_index()
df_produzione_weekly["Settimana"] = df_produzione_weekly["Data"].apply(label_settimana)

df_cassa["Saldo Netto"] = df_cassa["Entrate"] - df_cassa["Uscite"]
df_cassa_weekly = df_cassa.groupby(pd.Grouper(key="Data", freq="W-MON")).sum().reset_index()
df_cassa_weekly["Settimana"] = df_cassa_weekly["Data"].apply(label_settimana)

# Funzione per determinare l'andamento (per cruscotto)
def trend_indicator(series):
    if len(series) < 2:
        return "stable"
    diff = series.iloc[-1] - series.iloc[-2]
    if diff > 0:
        return "up"
    elif diff < 0:
        return "down"
    else:
        return "stable"

def draw_gauge(title, value, trend):
    color = {"up": "green", "down": "red", "stable": "orange"}.get(trend, "gray")
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [None, value * 1.5 if value > 0 else 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, value], 'color': color},
            ]
        }
    ))
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=300)
    return fig

st.subheader("📈 Indicatori settimanali")
st.plotly_chart(draw_gauge("📉 Weekly Costs", df_costi_weekly["Costo"].iloc[-1], trend_indicator(df_costi_weekly["Costo"])), use_container_width=True)
st.plotly_chart(draw_gauge("🏗️ Weekly Production", df_produzione_weekly["Quantità Prodotte"].iloc[-1], trend_indicator(df_produzione_weekly["Quantità Prodotte"])), use_container_width=True)
st.plotly_chart(draw_gauge("💰 Weekly Cash Flow", df_cassa_weekly["Saldo Netto"].iloc[-1], trend_indicator(df_cassa_weekly["Saldo Netto"])), use_container_width=True)

st.markdown("---")
st.subheader("📊 Grafici settimanali")

# Grafici
fig1 = px.line(df_costi_weekly, x="Settimana", y="Costo", title="Andamento settimanale dei costi")
fig2 = px.bar(df_produzione_weekly, x="Settimana", y="Quantità Prodotte", title="Produzione settimanale")
fig3 = px.line(df_cassa_weekly, x="Settimana", y="Saldo Netto", title="Andamento settimanale del saldo di cassa")

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

# Esportazione dati
st.markdown("---")
st.subheader("⬇️ Esporta i dati settimanali")

output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_costi_weekly.to_excel(writer, sheet_name='Costi Settimanali', index=False)
    df_produzione_weekly.to_excel(writer, sheet_name='Produzione Settimanale', index=False)
    df_cassa_weekly.to_excel(writer, sheet_name='Cassa Settimanale', index=False)
st.download_button("Download Excel riepilogativo", data=output.getvalue(), file_name="riepilogo_settimanale.xlsx")
