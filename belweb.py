import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Akıllı Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- EVRAK VE İŞLEM VERİTABANI (Asistanın Bilgi Kaynağı) ---
islem_rehberi = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı Almak": ["Tapu Fotokopisi", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi"],
        "Yapı Kullanma İzni (İskan)": ["Sığınak Raporu", "Enerji Kimlik Belgesi", "SSK İlişiksiz Belgesi"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Nüfus Kayıt Örneği", "Sağlık Raporu", "4 Adet Vesikalık Fotoğraf", "İkametgah"],
        "Dilekçe Sorgulama": ["TC Kimlik Kartı", "Dilekçe Kayıt Numarası"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Muafiyeti": ["Emeklilik Belgesi", "Tek Mesken Beyan Formu", "Tapu Örneği"],
        "Beyanname Verme": ["Tapu Fotokopisi", "Kimlik Fotokopisi"]
    }
}

# --- SESSION STATE AYARLARI ---
if "aktif_sekme_index" not in st.session_state:
    st.session_state.aktif_sekme_index = 0

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

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş Rehberi & Çözüm Merkezi")

st.divider()

# --- ANA SEKMELER (Otomatik Seçim Destekli) ---
# st.radio'yu menü gibi kullanarak sekmeler arası geçişi sağlıyoruz
secilen_islem = st.sidebar.radio("Menü", ["🤖 AI Belediye Asistanı", "📝 Yeni Şikayet Oluştur", "🔍 Şikayet Takibi"], index=st.session_state.aktif_sekme_index)

# --- MENÜ YÖNLENDİRME MANTIĞI ---
if secilen_islem == "🤖 AI Belediye Asistanı":
    st.header("🤖 Akıllı Belediye Asistanı")
    st.info("Size nasıl yardımcı olabilirim? Aşağıdaki seçeneklerden birini seçebilir veya bana yazabilirsiniz.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Şikayet Etmek İstiyorum"):
            st.session_state.aktif_sekme_index = 1
            st.rerun()
            
    with col2:
        if st.button("🔍 Şikayetimi Sorgulayacağım"):
            st.session_state.aktif_sekme_index = 2
            st.rerun()

    with col3:
        if st.button("📄 Evrak Bilgisi Alacağım"):
            st.session_state.evrak_modu = True

    st.write("---")
    
    # EVRAK BİLGİSİ SORGULAMA MODU
    if "evrak_modu" in st.session_state and st.session_state.evrak_modu:
        st.subheader("📑 İşlem & Evrak Rehberi")
        secilen_mud = st.selectbox("Lütfen İlgili Müdürlüğü Seçiniz:", list(islem_rehberi.keys()))
        secilen_islem_turu = st.selectbox("Yapmak İstediğiniz İşlemi Seçiniz:", list(islem_rehberi[secilen_mud].keys()))
        
        if st.button("Gereken Evrakları Göster"):
            evraklar = islem_rehberi[secilen_mud][secilen_islem_turu]
            st.warning(f"🔔 **{secilen_islem_turu}** işlemi için hazırlamanız gereken evraklar şunlardır:")
            for e in evraklar:
                st.write(f"- {e}")
            if st.button("Rehberi Kapat"):
                del st.session_state.evrak_modu
                st.rerun()

    # SOHBET KISMI
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Merhaba! Ben belediye asistanınız. Şikayet bildirimi yapabilir, evrak takibi yapabilir veya işlemler hakkında bilgi alabilirsiniz."}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Sorunuzu buraya yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # Akıllı Yanıtlar
        p_low = prompt.lower()
        if "şikayet" in p_low or "sikayet" in p_low:
            msg = "Şikayet oluşturma ekranına sol menüden ulaşabilir veya 'Şikayet Etmek İstiyorum' butonuna basabilirsiniz."
        elif "evrak" in p_low or "belge" in p_low:
            msg = "Yukarıdaki 'Evrak Bilgisi Alacağım' butonuna tıklayarak müdürlüklere göre gereken belgeleri listeleyebilirsiniz."
        else:
            msg = "Anlayamadım, lütfen yukarıdaki butonları kullanarak size daha hızlı yardımcı olmama izin verin."
            
        with st.chat_message("assistant"): st.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})

# --- TAB 1: ŞİKAYET OLUŞTURMA ---
elif secilen_islem == "📝 Yeni Şikayet Oluştur":
    st.header("📝 Yeni Şikayet Formu")
    # ... (Buradaki form kodun önceki şikayet formunla aynı olacak)
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız", key="ad_y")
        eposta = st.text_input("E-posta", key="ep_y")
    with c2:
        soyad = st.text_input("Soyadınız", key="so_y")
        tel = st.text_input("Telefon", key="te_y")
    
    detay = st.text_area("Şikayetiniz")
    if st.button("Kaydet"):
        st.success("Kaydedildi!")

# --- TAB 2: SORGULAMA ---
elif secilen_islem == "🔍 Şikayet Takibi":
    st.header("🔍 Şikayet Takip Paneli")
    # ... (Önceki sorgulama kodun)
    sorgu = st.text_input("Takip numaranızı veya telefonunuzu girin")
    if st.button("Sorgula"):
        st.write("Sonuçlar yükleniyor...")

# --- MÜDÜRLÜK PANELİ (Expander) ---
st.write("---")
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    pass # Önceki yönetim paneli kodun buraya gelecek
