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

# --- SESSION STATE (Sayfa Yönetimi ve Sohbet) ---
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "asistan"
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- BİLGİ BANKASI ---
BELEDİYE_BİLGİLERİ = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "çalışma_saatleri": "Hafta içi 08:30 - 17:30",
}

evrak_rehberi = {
    "İmar Müdürlüğü": "Tapu, Mimari Proje, İmar Durum Belgesi.",
    "Yazı İşleri": "Kimlik Fotokopisi, Islak İmzalı Dilekçe.",
    "Nikah İşlemleri": "Sağlık Raporu, 4 Fotoğraf, Nüfus Kayıt Örneği."
}

sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}

# --- YARDIMCI FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, encoding="utf-8-sig")
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

# --- 🤖 1. BÖLÜM: ANA ASİSTAN EKRANI ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Merhaba! Ondokuzmayıs Belediyesi Akıllı Asistanına hoş geldiniz. 😊 \n\nSize nasıl yardımcı olabilirim? \n\n**Örn:** Şikayet oluşturmak, şikayetimi sorgulamak veya evrak bilgisi almak istiyorum diyebilirsiniz."
        })

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Mesajınızı buraya yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        p_low = prompt.lower()
        
        # Akıllı Yönlendirme ve Cevaplama
        if any(x in p_low for x in ["şikayet", "sikayet", "oluştur", "bildir"]):
            ans = "Anladım, sizi hemen şikayet oluşturma formuna yönlendiriyorum..."
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.sayfa = "sikayet_olustur"
            st.rerun()
            
        elif any(x in p_low for x in ["sorgu", "takip", "durum", "nerede"]):
            ans = "Şikayetinizi sorgulamanız için paneli açıyorum..."
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.sayfa = "sorgulama"
            st.rerun()
            
        elif any(x in p_low for x in ["evrak", "belge", "gereken"]):
            ans = f"Evrak Bilgileri: \n\n" + "\n".join([f"**{k}**: {v}" for k, v in evrak_rehberi.items()])
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()
            
        elif any(x in p_low for x in ["konum", "adres", "belediye nerede"]):
            ans = f"📍 Belediyemiz: {BELEDİYE_BİLGİLERİ['konum']}"
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()
            
        else:
            ans = "Size şikayet oluşturma, sorgulama ve evrak bilgisi konularında yardımcı olabilirim. Lütfen yapmak istediğiniz işlemi belirtin."
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

# --- 📝 2. BÖLÜM: YENİ ŞİKAYET FORMU (ASİSTAN ATADIKTAN SONRA) ---
elif st.session_state.sayfa == "sikayet_olustur":
    st.header("📝 Yeni Şikayet Formu")
    if st.button("⬅️ Asistana Geri Dön"): 
        st.session_state.sayfa = "asistan"
        st.rerun()

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="f_ad")
            eposta = st.text_input("E-posta Adresiniz", key="f_mail")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = False
            if eposta != "": 
                if re.match(email_pattern, eposta, re.IGNORECASE):
                    st.success("E-posta formatı geçerli. ✅")
                    is_email_valid = True
                else: st.warning("⚠️ Lütfen geçerli bir e-posta uzantısı giriniz!")

        with c2:
            soyad = st.text_input("Soyadınız", key="f_soyad")
            tel_input = st.text_input("Telefon Numaranız", key="f_tel")

        tum_birimler = sorted(list(sikayet_turleri_dict.keys()))
        secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler)
        tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel", "Diğer"])
        sikayet_turu = st.selectbox("Şikayet Türü (Öneriler)", tur_listesi)
        detay = st.text_area("Şikayet Detayı")

        if st.button("Şikayeti Kaydet"):
            if ad and soyad and is_email_valid and tel_input and detay:
                temiz_tel = tel_temizle(tel_input)
                # Kayıt işlemleri buraya (CSV Yazma)
                st.success("✅ Şikayetiniz başarıyla kaydedildi!")
                st.balloons()
            else: st.error("Lütfen tüm alanları doğru formatta doldurunuz!")

# --- 🔍 3. BÖLÜM: SORGULAMA EKRANI ---
elif st.session_state.sayfa == "sorgulama":
    st.header("🔍 Şikayet Sorgulama")
    if st.button("⬅️ Asistana Geri Dön"): 
        st.session_state.sayfa = "asistan"
        st.rerun()
    
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
    if arama:
        # Sorgulama mantığın buraya gelecek
        st.info("Kayıtlar aranıyor...")

# --- 🏢 MÜDÜRLÜK PANELİ (ŞİFRELİ) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    sifre = st.text_input("Giriş Şifresi", type="password")
    if sifre == "1234":
        st.success("Yetkili Girişi Başarılı.")
        # Yönetim kodların...
    elif sifre != "": st.error("Hatalı Şifre!")
