import streamlit as st
import plotly.graph_objects as go
import numpy as np
from analiz import bist_hisse_analiz, tum_hisseleri_tara
from config import POPULER_HISSELER

# Sayfa Konfigürasyonu (Mobil Uyumlu)
st.set_page_config(
    page_title="Robotcan Borsa Terminali",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Koyu Tema CSS Özelleştirmeleri
st.markdown("""
<style>
    .stApp { background-color: #11111b; color: #cdd6f4; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .metric-box { background-color: #1e1e2e; padding: 15px; border-radius: 10px; border: 1px solid #313244; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 ROBOTCAN Borsa Terminali")
st.caption("BIST Mum Formasyon Taraması & Teknik Analiz Platformu")

# Hızlı Seçim Butonları
st.write("🔥 **Popüler BIST Hisseleri:**")
cols = st.columns(len(POPULER_HISSELER[:8]))
secilen_hisse = None

for i, sembol in enumerate(POPULER_HISSELER[:8]):
    if cols[i].button(sembol, key=f"btn_{sembol}"):
        secilen_hisse = sembol

# Arama ve Tarama Alanı
col_input, col_btn1, col_btn2 = st.columns([2, 1, 1.5])

with col_input:
    girilen_hisse = st.text_input("Hisse Kodu Girin:", value=secilen_hisse if secilen_hisse else "THYAO").upper().strip()

with col_btn1:
    st.write("")
    st.write("")
    btn_analiz = st.button("🔍 Analiz Et", type="primary")

with col_btn2:
    st.write("")
    st.write("")
    btn_tara = st.button("🔥 Tüm BIST'i Tara")

# --- TÜM BIST TARAMA MODU ---
if btn_tara:
    st.subheader("🚀 BIST Tüm Hisseler Taranıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_guncelle(suanki, toplam, sembol):
        progress_bar.progress(suanki / toplam)
        status_text.text(f"İnceleniyor: [{suanki}/{toplam}] {sembol}")

    bulunanlar = tum_hisseleri_tara(progress_callback=progress_guncelle)
    progress_bar.empty()
    status_text.empty()

    if bulunanlar:
        st.success(f"🎯 **{len(bulunanlar)} Hissede Güçlü AL Kırılımı Bulundu!**")
        for b in bulunanlar:
            st.markdown(f"👉 **{b['sembol']}** | Tarih: `{b['tarih']}` | Kapanış: `{b['kapanis']} TL` | Kırılan Tepe: `{b['direnc']} TL`")
    else:
        st.warning("Son haftalarda bu stratejiye uyan yeni sinyal bulunamadı.")

# --- TEK HİSSE ANALİZ MODU ---
elif btn_analiz or girilen_hisse:
    with st.spinner(f"{girilen_hisse} verileri alınıyor..."):
        veri = bist_hisse_analiz(girilen_hisse)

    if not veri.get("basari"):
        st.error(f"Hata: {veri.get('mesaj')}")
    else:
        col_sol, col_sag = st.columns([1, 2])

        with col_sol:
            st.subheader(f"📊 {veri['sembol']} Özet Rapor")
            degisim_renk = "normal" if veri['gunluk_degisim'] >= 0 else "inverse"
            st.metric("Son Fiyat", f"{veri['son_fiyat']} TL", f"%{veri['gunluk_degisim']}")

            st.write(f"**📦 Hacim:** {veri['son_hacim']:,}")
            st.write(f"**🎯 RSI (14):** {veri['rsi']}")
            st.write(f"**📈 SMA 20 / SMA 50:** {veri['sma_20']} TL / {veri['sma_50']} TL")
            
            st.markdown("---")
            st.markdown("💡 **Sinyaller & Strateji:**")
            for s in veri['sinyaller']:
                st.info(s)

        with col_sag:
            st.subheader("🕯️ Haftalık Mum Grafiği (Son 1 Yıl)")
            df_plot = veri.get("haftalik_veri")

            if df_plot is not None and not df_plot.empty:
                # Plotly ile Mobil Uyumlu Dokunmatik Mum Grafiği
                fig = go.Figure()

                # Mumlar
                fig.add_trace(go.Candlestick(
                    x=df_plot.index,
                    open=df_plot['Open'],
                    high=df_plot['High'],
                    low=df_plot['Low'],
                    close=df_plot['Close'],
                    name="Mumlar",
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ))

                # Formasyon Sinyal Noktaları (▲ İşaretçileri)
                formasyonlar = veri.get("formasyon_noktalari", [])
                for f in formasyonlar:
                    idx = f["indeks"]
                    if idx < len(df_plot):
                        tarih = df_plot.index[idx]
                        fiyat = float(df_plot['Low'].iloc[idx]) * 0.96
                        fig.add_annotation(
                            x=tarih, y=fiyat,
                            text="▲ AL",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor="#f9e2af",
                            font=dict(color="#f9e2af", size=12, family="Arial Black"),
                            bgcolor="#181825"
                        )

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#181825",
                    plot_bgcolor="#181825",
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=520
                )
                st.plotly_chart(fig, use_container_width=True)