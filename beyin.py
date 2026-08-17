import re
from analiz import bist_hisse_analiz, tum_hisseleri_tara

def hisse_kodu_yakala(metin: str) -> str:
    kelimeler = re.findall(r'\b[A-Za-z0-9]{3,6}\b', metin.upper())
    for kelime in kelimeler:
        if kelime not in ["ANALIZ", "NEDIR", "BORSA", "HISSE", "NASIL", "AL", "SAT", "FIYAT", "TARA"]:
            return kelime
    return metin.strip().upper()

def rapor_olustur(veri: dict) -> str:
    if not veri.get("basari"):
        return f"⚠️ **Hata:** {veri.get('mesaj', 'Bilinmeyen bir hata oluştu.')}"

    sembol = veri["sembol"]
    degisim = veri["gunluk_degisim"]
    degisim_yazi = f"+%{degisim}" if degisim >= 0 else f"%{degisim}"
    sinyal_metni = "\n".join([f"{s}" for s in veri['sinyaller']])

    return (
        f"📊 **{sembol} - Strateji & Teknik Rapor**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 **Son Kapanış:** {veri['son_fiyat']} TL ({degisim_yazi})\n"
        f"📦 **Hacim:** {veri['son_hacim']:,} (20G Ort: {veri['hacim_20_ort']:,})\n"
        f"🎯 **RSI (14):** {veri['rsi']}\n"
        f"📈 **SMA 20:** {veri['sma_20']} TL | **SMA 50:** {veri['sma_50']} TL\n\n"
        f"💡 **Özel Formasyon Taraması (Yeşil-Kırmızı-Kırmızı-Yeşil):**\n"
        f"{sinyal_metni}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Not: Otomatik teknik analizdir. Yatırım tavsiyesi değildir.*"
    )

def zeki_cevap(kullanici_mesaji: str) -> tuple:
    if not kullanici_mesaji.strip():
        return "Lütfen analiz edilecek hisse kodunu girin.", None

    sembol = hisse_kodu_yakala(kullanici_mesaji)
    veri = bist_hisse_analiz(sembol)

    if not veri.get("basari"):
        return f"⚠️ Hata: {veri.get('mesaj')}", None

    rapor = rapor_olustur(veri)
    return rapor, veri