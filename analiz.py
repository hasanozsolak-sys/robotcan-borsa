import yfinance as yf
import pandas as pd
import numpy as np
import ta
from config import BIST_TUM_HISSELER

def haftalik_formasyon_tara(sembol: str) -> dict:
    sembol = sembol.upper().strip()
    ticker_str = f"{sembol}.IS" if not sembol.endswith(".IS") else sembol

    try:
        df_haftalik = yf.download(ticker_str, period="1y", interval="1wk", progress=False, timeout=10)

        if df_haftalik is None or df_haftalik.empty:
            return {"basari": False, "mesaj": "Yetersiz haftalık veri."}

        if isinstance(df_haftalik.columns, pd.MultiIndex):
            df_haftalik.columns = df_haftalik.columns.get_level_values(0)

        # Boş ve hatalı satırları temizle
        df_haftalik = df_haftalik.dropna(subset=['Open', 'High', 'Low', 'Close'])
        if len(df_haftalik) < 5:
            return {"basari": False, "mesaj": "Yetersiz haftalık veri."}

        bulunan_formasyonlar = []

        for i in range(3, len(df_haftalik)):
            m1 = df_haftalik.iloc[i-3]
            m2 = df_haftalik.iloc[i-2]
            m3 = df_haftalik.iloc[i-1]
            m4 = df_haftalik.iloc[i]

            m1_yesil = float(m1['Close']) > float(m1['Open'])
            m2_kirmizi = float(m2['Close']) < float(m2['Open'])
            m3_kirmizi = float(m3['Close']) < float(m3['Open'])
            m4_yesil = float(m4['Close']) > float(m4['Open'])

            kirmizi_zirve = max(float(m2['High']), float(m3['High']))
            kirilim_var = float(m4['Close']) > kirmizi_zirve

            if m1_yesil and m2_kirmizi and m3_kirmizi and m4_yesil and kirilim_var:
                tarih_str = df_haftalik.index[i].strftime("%d.%m.%Y")
                bulunan_formasyonlar.append({
                    "indeks": i,
                    "tarih": tarih_str,
                    "kapanis": round(float(m4['Close']), 2),
                    "direnc": round(float(kirmizi_zirve), 2)
                })

        return {
            "basari": True,
            "formasyonlar": bulunan_formasyonlar,
            "df_haftalik": df_haftalik
        }
    except Exception as e:
        return {"basari": False, "mesaj": str(e)}

def tum_hisseleri_tara(progress_callback=None) -> list:
    bulunanlar = []
    toplam = len(BIST_TUM_HISSELER)

    for i, sembol in enumerate(BIST_TUM_HISSELER):
        if progress_callback:
            progress_callback(i + 1, toplam, sembol)
        
        try:
            sonuc = haftalik_formasyon_tara(sembol)
            if sonuc.get("basari") and sonuc.get("formasyonlar"):
                son_formasyon = sonuc["formasyonlar"][-1]
                toplam_mum = len(sonuc["df_haftalik"])
                
                if son_formasyon["indeks"] >= toplam_mum - 2:
                    bulunanlar.append({
                        "sembol": sembol,
                        "tarih": son_formasyon["tarih"],
                        "kapanis": son_formasyon["kapanis"],
                        "direnc": son_formasyon["direnc"]
                    })
        except Exception:
            continue

    return bulunanlar

def bist_hisse_analiz(sembol: str) -> dict:
    sembol = sembol.upper().strip()
    ticker_str = f"{sembol}.IS" if not sembol.endswith(".IS") else sembol

    try:
        df = yf.download(ticker_str, period="6mo", interval="1d", progress=False, timeout=10)
        
        if df is None or df.empty:
            return {"basari": False, "mesaj": f"'{sembol}' için veri bulunamadı."}

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Boş satırları temizle
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        if len(df) < 20:
            return {"basari": False, "mesaj": f"'{sembol}' için yeterli geçmiş veri yok."}

        son_fiyat = float(df['Close'].iloc[-1])
        onceki_kapanis = float(df['Close'].iloc[-2])
        gunluk_degisim = ((son_fiyat - onceki_kapanis) / onceki_kapanis) * 100
        son_hacim = int(df['Volume'].iloc[-1])
        hacim_20gun_ort = int(df['Volume'].tail(20).mean())

        # İndikatörler
        close_series = df['Close'].squeeze()
        rsi_series = ta.momentum.RSIIndicator(close=close_series, window=14).rsi().dropna()
        rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0

        sma_20_series = df['Close'].rolling(window=20).mean().dropna()
        sma_50_series = df['Close'].rolling(window=50).mean().dropna()
        sma_20 = float(sma_20_series.iloc[-1]) if not sma_20_series.empty else son_fiyat
        sma_50 = float(sma_50_series.iloc[-1]) if not sma_50_series.empty else son_fiyat

        tarama = haftalik_formasyon_tara(sembol)

        sinyaller = []
        if tarama.get("basari") and tarama.get("formasyonlar"):
            adet = len(tarama["formasyonlar"])
            sinyaller.append(f"🎯 Son 1 yılda stratejiye uyan {adet} adet AL sinyali noktası bulundu:")
            for item in tarama["formasyonlar"]:
                sinyaller.append(f"  ➜ Hafta: {item['tarih']} | Kapanış: {item['kapanis']} TL | Kırılan Direnç: {item['direnc']} TL")
        else:
            sinyaller.append("⚪ Son 1 yılda bu 4'lü formasyon şartını sağlayan sinyal henüz oluşmadı.")

        return {
            "basari": True,
            "sembol": sembol,
            "son_fiyat": round(son_fiyat, 2),
            "gunluk_degisim": round(gunluk_degisim, 2),
            "son_hacim": son_hacim,
            "hacim_20_ort": hacim_20gun_ort,
            "rsi": round(rsi, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sinyaller": sinyaller,
            "gecmis_veri": df,
            "haftalik_veri": tarama.get("df_haftalik"),
            "formasyon_noktalari": tarama.get("formasyonlar", [])
        }
    except Exception as e:
        return {"basari": False, "mesaj": str(e)}
