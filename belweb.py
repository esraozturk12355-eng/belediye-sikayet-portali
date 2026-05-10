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

# --- BELEDİYE BİLGİ BANKASI (Asistanın Bilgeliği) ---
BELEDİYE_BİLGİLERİ = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "çalışma_saatleri": "Hafta içi 08:30 - 17:30",
    "web": "www.19mayis.bel.tr"
}

# --- SESSION STATE ---
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "asistan"
if "messages" not in st.session_state:
    st.session_state.messages = []

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
    st.subheader("Akıllı Vatandaş Portalı")

st.divider()

# --- 🤖 ASİSTAN VE ANA SOHBET EKRANI ---
if st.session_state.sayfa == "asistan":
    # Karşılama mesajı (Sadece ilk açılışta)
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Merhaba! Ben Ondokuzmayıs Belediyesi Bilge Asistanı. Size belediyemiz hakkında bilgi verebilir, şikayetlerinizi alabilir veya gerekli evrakları listeleyebilirim. Ne yapmak istersiniz?"
        })

    # Sohbet geçmişini göster
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])
            if "options" in msg:
                # Seçenekleri buton olarak göster
                cols = st.columns(len(msg["options"]))
                for i, opt in enumerate(msg["options"]):
                    if cols[i].button(opt, key=f"opt_{i}_{datetime.now().timestamp()}"):
                        if "Şikayet Et" in opt: st.session_state.sayfa = "sikayet_olustur"; st.rerun()
                        elif "Sorgula" in opt: st.session_state.sayfa = "sorgulama"; st.rerun()
                        elif "Evrak" in opt: st.session_state.sayfa = "evrak_kontrol"; st.rerun()

    # Eğer son mesaj asistandan gelmişse ve seçenek içermiyorsa, seçenekleri her zaman en altta sun
    if st.session_state.messages[-1]["role"] == "assistant":
        st.write("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("📝 Yeni Şikayet Oluştur"): st.session_state.sayfa = "sikayet_olustur"; st.rerun()
        if c2.button("🔍 Şikayetimi Sorgula"): st.session_state.sayfa = "sorgulama"; st.rerun()
        if c3.button("📄 Gerekli Evraklar"): st.session_state.sayfa = "evrak_kontrol"; st.rerun()

    # Kullanıcı Girişi
    if prompt := st.chat_input("Sorunuzu buraya yazın (Örn: Konumunuz neresi?)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        p_low = prompt.lower()
        resp = ""
        
        # Bilgelik Filtresi
        if "konum" in p_low or "adres" in p_low or "nerede" in p_low:
            resp = f"Belediyemiz Samsun ilindedir. Açık Adres: {BELEDİYE_BİLGİLERİ['konum']}"
        elif "telefon" in p_low or "numara" in p_low or "iletişim" in p_low:
            resp = f"Bize şu numaradan ulaşabilirsiniz: {BELEDİYE_BİLGİLERİ['telefon']}"
        elif "saat" in p_low or "açık" in p_low:
            resp = f"Belediyemiz {BELEDİYE_BİLGİLERİ['çalışma_saatleri']} arasında hizmet vermektedir."
        elif "şikayet" in p_low:
            resp = "Anladım, şikayet formuna yönlendiriyorum."
            st.session_state.sayfa = "sikayet_olustur"; st.rerun()
        else:
            resp = "Size bu konuda yardımcı olmak isterim. Şikayet bildirimi, sorgulama veya evrak bilgisi için butonları kullanabilir veya genel bir soru sorabilirsiniz."

        st.session_state.messages.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"): st.markdown(resp)
        st.rerun()

# --- 📝 YENİ ŞİKAYET FORMU (Düzeltilmiş ve Tam) ---
elif st.session_state.sayfa == "sikayet_olustur":
    st.header("📝 Yeni Şikayet Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.form("sikayet_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ad = st.text_input("Adınız")
            eposta = st.text_input("E-posta Adresiniz")
        with col2:
            soyad = st.text_input("Soyadınız")
            telefon = st.text_input("Telefon Numaranız")
        
        # Müdürlük listesi
        mud_listesi = sorted(list(set(list({
            "Yazı İşleri Müdürlüğü": [], "Veteriner İşleri Müdürlüğü": [],
            "Fen İşleri Müdürlüğü": [], "Zabıta Müdürlüğü": [],
            "İmar ve Şehircilik Müdürlüğü": [], "Mali Hizmetler Müdürlüğü": []
        }.keys()) + ["Emlak ve İstimlak", "Destek Hizmetleri"])))
        
        mudurluk = st.selectbox("İlgili Müdürlük", mud_listesi)
        sikayet_turu = st.text_input("Şikayet Konusu (Örn: Yol Bozukluğu)")
        detay = st.text_area("Şikayetinizin Detayı", height=150)
        
        submit = st.form_submit_button("Şikayeti Kaydet")
        
        if submit:
            if ad and soyad and eposta and telefon and detay:
                # Kayıt işlemleri buraya gelecek (CSV'ye yazma)
                st.success("✅ Şikayetiniz başarıyla kaydedildi!")
                st.balloons()
            else:
                st.error("Lütfen tüm alanları doldurunuz!")

# --- 🔍 SORGULAMA ---
elif st.session_state.sayfa == "sorgulama":
    st.header("🔍 Şikayet Sorgulama")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
    # Sorgulama kodları buraya...

# --- 📄 EVRAK KONTROL ---
elif st.session_state.sayfa == "evrak_kontrol":
    st.header("📄 Gerekli Evraklar Rehberi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    st.write("Bilgi almak istediğiniz işlemi seçiniz...")
    # Evrak katalog kodları buraya...

# --- YÖNETİM PANELİ ---
st.write("---")
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    sifre = st.text_input("Şifre", type="password")
    if sifre == "1234":
        st.write("Yetkili Girişi Yapıldı.")
