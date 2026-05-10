import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi AI Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- EVRAK VERİTABANI (Tüm Müdürlükler İçin) ---
evrak_katalogu = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Fotokopisi", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi"],
        "İskan Alımı": ["Sığınak Raporu", "Enerji Kimlik Belgesi", "SSK İlişiksiz Belgesi"],
        "Yıkım Ruhsatı": ["Emlak Vergi Borcu Yoktur Yazısı", "İlgili Kurumlardan İlişiksiz Belgesi"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Nüfus Kayıt Örneği", "Sağlık Raporu", "4 Adet Fotoğraf", "İkametgah"],
        "Dilekçe Verme": ["TC Kimlik Kartı", "Islak İmzalı Dilekçe"],
        "Bilgi Edinme": ["Başvuru Formu", "Kimlik Fotokopisi"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Muafiyeti": ["Emeklilik Belgesi", "Tek Mesken Beyan Formu", "Tapu Örneği"],
        "İşyeri Açma Vergisi": ["Vergi Levhası", "Kira Kontratı", "Esnaf Sicil Gazetesi"],
        "Rayiç Değer Belgesi": ["Tapu Örneği", "Kimlik Aslı"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Tapu Fotokopisi", "İtfaiye Uygunluk Raporu"],
        "Hafta Tatili Ruhsatı": ["Ruhsat Fotokopisi", "Harç Makbuzu"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Evcil Hayvan Kaydı": ["Hayvanın Pasaportu", "Kuduz Aşısı Kartı", "Sahibinin Kimliği"],
        "Sokak Hayvanı Şikayeti": ["Konum Bilgisi", "Olay Fotoğrafı (Varsa)"]
    },
    "Fen İşleri Müdürlüğü": {
        "Asfalt Katılım Payı Sorgulama": ["Ada/Parsel Bilgisi", "Kimlik Fotokopisi"],
        "Yol Kazı İzni": ["Proje Örneği", "Kazı Ruhsat Talep Formu"]
    }
}

# --- SESSION STATE (Süreç Yönetimi) ---
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "asistan"

# --- YARDIMCI FONKSİYONLAR ---
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

# --- LOGO VE BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Yapay Zeka Destekli Vatandaş Portalı")

st.divider()

# --- ANA MANTIĞI YÖNETEN ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.info("### 🤖 Hoş geldiniz! Ben Belediye Asistanınız.\nSize nasıl yardımcı olabilirim? Lütfen bir seçenek belirleyin veya bana yazın.")
    
    # Hızlı Seçenek Butonları
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("📝 Yeni Şikayet Oluştur"):
            st.session_state.sayfa = "sikayet_olustur"
            st.rerun()
    with btn_col2:
        if st.button("🔍 Şikayet Sorgula"):
            st.session_state.sayfa = "sorgulama"
            st.rerun()
    with btn_col3:
        if st.button("📄 Gerekli Evrakları Görüntüle"):
            st.session_state.sayfa = "evrak_kontrol"
            st.rerun()

    st.write("---")
    
    # Sohbet Kutusu (Kullanıcı Yazarsa)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Mesajınızı buraya yazabilirsiniz..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        p_low = prompt.lower()
        if "şikayet" in p_low or "sikayet" in p_low:
            resp = "Şikayet kaydı oluşturmanız için sizi ilgili forma yönlendiriyorum."
            st.session_state.sayfa = "sikayet_olustur"
            st.rerun()
        elif "sorgu" in p_low or "takip" in p_low:
            resp = "Sorgulama ekranına yönlendiriliyorsunuz."
            st.session_state.sayfa = "sorgulama"
            st.rerun()
        elif "evrak" in p_low or "belge" in p_low:
            resp = "Evrak kontrolü için sizi rehberimize yönlendiriyorum."
            st.session_state.sayfa = "evrak_kontrol"
            st.rerun()
        else:
            resp = "Şu an için size şikayet oluşturma, sorgulama ve evrak bilgisi konularında yardımcı olabilirim. Lütfen bu işlemlerden birini belirtin."
        
        st.session_state.messages.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"): st.markdown(resp)

# --- EVRAK KONTROL EKRANI ---
elif st.session_state.sayfa == "evrak_kontrol":
    st.header("📑 Müdürlük Bazlı Gerekli Evraklar")
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"
        st.rerun()
    
    st.write("Bilgi almak istediğiniz müdürlüğü seçiniz:")
    secilen_mud = st.selectbox("Müdürlük Seçimi", list(evrak_katalogu.keys()))
    
    if secilen_mud:
        st.write(f"**{secilen_mud}** bünyesinde yapabileceğiniz işlemler:")
        islem = st.selectbox("İşlem Seçimi", list(evrak_katalogu[secilen_mud].keys()))
        
        if islem:
            st.warning(f"📌 **{islem}** için hazırlamanız gereken evrak listesi:")
            for e in evrak_katalogu[secilen_mud][islem]:
                st.write(f"- {e}")

# --- ŞİKAYET OLUŞTURMA EKRANI ---
elif st.session_state.sayfa == "sikayet_olustur":
    st.header("📝 Yeni Şikayet Formu")
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"
        st.rerun()
    
    # Form içeriği (Kaan, senin form kodun buraya gelecek)
    st.info("Lütfen aşağıdaki formu doldurunuz.")
    # (Örnek alanlar)
    ad = st.text_input("Adınız")
    soyad = st.text_input("Soyadınız")
    # ... formun devamı ...

# --- SORGULAMA EKRANI ---
elif st.session_state.sayfa == "sorgulama":
    st.header("🔍 Şikayet Takip Paneli")
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"
        st.rerun()
    
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
    # ... sorgulama kodun ...

# --- YÖNETİM PANELİ (Her zaman en altta gizli kalsın) ---
st.write("---")
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    sifre = st.text_input("Giriş Şifresi", type="password")
    if sifre == "1234":
        st.success("Yönetim paneli aktif.")
        # ... yönetim kodun ...
