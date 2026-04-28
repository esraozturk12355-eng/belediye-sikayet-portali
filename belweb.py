import streamlit as st
import pandas as pd
import os
import re
import urllib.parse # Mesajları WhatsApp linkine çevirmek için
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide", initial_sidebar_state="collapsed")

# --- WHATSAPP LINK OLUSTURMA FONKSIYONU ---
def wp_link_olustur(telefon, mesaj):
    # Telefonun başındaki sıfırı atıp Türkiye kodu ekliyoruz (90)
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

# ... (Müdürlük listeleri aynı kalıyor) ...

st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

# --- TAB 1: YENİ ŞİKAYET ---
with tab1:
    st.header("Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız", key="ad_yeni")
        eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
    with c2: 
        soyad = st.text_input("Soyadınız", key="soyad_yeni")
        telefon_input = st.text_input("Telefon Numaranız (0 olmadan giriniz)", key="tel_yeni")
    
    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_yeni")
    detay = st.text_area("Şikayet Detayı", key="detay_yeni")
    
    if st.button("Şikayeti Kaydet"):
        if ad and soyad and telefon_input:
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            # Kayıt işlemi (Özet)
            yeni_kayit = {"ID": sikayet_id, "Ad": ad, "Telefon": telefon_input, "Müdürlük": secilen_mudurluk, "Durum": "İnceleniyor"}
            pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            
            st.success(f"✅ Şikayet Alındı. ID: {sikayet_id}")
            
            # --- WHATSAPP BUTONU ---
            wp_mesaj = f"Sayın {ad} {soyad}, {sikayet_id} numaralı şikayet talebiniz alınmıştır. En kısa sürede incelenecektir."
            link = wp_link_olustur(telefon_input, wp_mesaj)
            st.markdown(f'''<a href="{link}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">📱 Vatandaşa WhatsApp'tan Bildir</button></a>''', unsafe_allow_html=True)

# --- MÜDÜRLÜK PANELİ (Güncelleme ve WP Bildirimi) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    sifre = st.text_input("Şifre:", type="password", key="admin_sifre")
    if sifre == "1234":
        df = veri_yukle()
        if not df.empty:
            secilen_id = st.selectbox("ID Seçiniz:", df["ID"].tolist(), key="id_sec")
            yeni_durum = st.selectbox("Durum:", ["İşleme Alındı", "Tamamlandı", "Reddedildi"], key="durum_sec")
            cevap = st.text_area("Cevap Notu:", key="cevap_sec")
            
            if st.button("Güncelle ve WP Linki Oluştur"):
                idx = df[df["ID"] == secilen_id].index
                alici_ad = df.at[idx[0], "Ad"]
                alici_tel = df.at[idx[0], "Telefon"]
                
                # Güncelleme
                df.at[idx[0], "Durum"] = yeni_durum
                df.at[idx[0], "Belediye_Cevabi"] = cevap
                df.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                
                st.success("Veri güncellendi!")
                
                # --- GÜNCELLEME İÇİN WP BUTONU ---
                guncel_mesaj = f"Sayın {alici_ad}, {secilen_id} numaralı şikayetiniz güncellenmiştir.\nDurum: {yeni_durum}\nCevap: {cevap}"
                link = wp_link_olustur(alici_tel, guncel_mesaj)
                st.markdown(f'''<a href="{link}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">📱 Güncellemeyi WhatsApp'tan Gönder</button></a>''', unsafe_allow_html=True)
