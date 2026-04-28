import streamlit as st
import pandas as pd
import os
import re
import urllib.parse
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Şikayet Portalı", 
    layout="wide",
    initial_sidebar_state="collapsed", # Varsayılan olarak kapalı tutar
    page_icon="🏛️"
)

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 8]) # Logo için dar, başlık için geniş sütun
with c1:
    # Simetrik bir logo kullanıyoruz. Ankara Büyükşehir Belediyesi logosu (Arama sonucu #8 veya #9)
    # Ya da genel bir 'Ondokuzmayıs' simgesi.
    st.image("https://upload.wikimedia.org/wikipedia/tr/a/a1/Ankara_B%C3%BCy%C3%BCk%C5%9Fehir_Belediyesi_logosu.png", width=80) 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Şikayet Yönetim Portalı")

st.divider()

# --- WHATSAPP LINK OLUSTURMA FONKSIYONU ---
def wp_link_olustur(telefon, mesaj):
    temiz_tel = str(telefon).strip()
    if temiz_tel.startswith("0"):
        temiz_tel = temiz_tel[1:]
    encoded_mesaj = urllib.parse.quote(mesaj)
    link = f"https://wa.me/90{temiz_tel}?text={encoded_mesaj}"
    return link

# --- VERİ YÜKLEME ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"): return tel[1:]
    return tel

# ... (Müdürlük listeleri ve TAB yapıları aynı kalıyor) ...

tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

# ... (Yeni Şikayet Oluşturma TAB1 aynı kalıyor, sadece ana başlıkları sadeleştirdim)
with tab1:
    st.markdown("#### 📝 Yeni Şikayet Formu")
    # ... (kodun geri kalanı aynı)

with tab2:
    st.markdown("#### 🔍 Şikayet Sorgulama")
    # ... (kodun geri kalanı aynı)

# --- MÜDÜRLÜK PANELİ (Aynı kalıyor) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    # ... (kodun geri kalanı aynı)
