import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Şikayet Portalı", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- 📚 TÜM MÜDÜRLÜKLERİ KAPSAYAN EVRAK REHBERİ ---
EVRAK_REHBERI = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Kaydı", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi"],
        "Yapı Kullanma İzin Belgesi (İskan)": ["Enerji Kimlik Belgesi", "Sığınak Raporu", "SGK İlişiksiz Belgesi"],
        "Numarataj İşlemleri": ["Tapu Fotokopisi", "Yapı Ruhsatı", "Kimlik Fotokopisi"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Sağlık Raporu", "4 Adet Fotoğraf", "Nüfus Kayıt Örneği", "Kimlik Aslı"],
        "Dilekçe Kayıt": ["Islak İmzalı Dilekçe", "Kimlik Bilgisi", "İletişim Bilgileri"],
        "Encümen Kararı Örneği": ["Dilekçe", "İlgili Kararın Tarih ve Sayısı"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Kısıtlılık Belgesi (Varsa)"],
        "Rayiç Bedel Belgesi": ["Tapu Fotokopisi", "Borçsuzluk Yazısı", "İlgili Kişinin Kimliği"],
        "İlan ve Reklam Vergisi": ["Tabela Ölçüleri", "Vergi Levhası Fotokopisi", "Dilekçe"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Uygunluk Raporu", "Oda Kayıt Belgesi"],
        "Hafta Tatili Ruhsatı": ["Ruhsat Fotokopisi", "Dilekçe"],
        "Pazar Yeri Tahsisi": ["Oda Kayıt Belgesi", "İkametgah", "Sabıka Kaydı"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe veya Fotoğraflı Kanıt"],
        "Alt Yapı Kazı İzni": ["Proje Onayı", "AYKOME İzin Belgesi", "Teminat Dekontu"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası"],
        "Sokak Hayvanı Tedavi Talebi": ["İhbar Dilekçesi veya Sözlü Beyan", "Konum Bilgisi"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Belediye Taşınmaz Kiralama": ["İhale Şartnamesi", "Geçici Teminat Makbuzu", "İkametgah"],
        "Yer Tahsis Talebi": ["Kurumsal Yazı veya Şahsi Dilekçe", "Kullanım Amacı Belgesi"]
    },
    "Temizlik İşleri / Sıfır Atık": {
        "Çöp Konteynırı Talebi": ["Dilekçe", "Bina Sakinleri İmzası (Gerekirse)"],
        "Geri Dönüşüm Eğitimi": ["Başvuru Formu"]
    }
}

BELEDİYE_İLETİŞİM = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "saat": "Hafta içi 08:30 - 17:30"
}

# --- SESSION STATE ---
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "asistan"
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LOGO VE BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş Çözüm Merkezi")

st.divider()

# --- YARDIMCI FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def tel_temizle(tel):
    tel = str(tel).strip()
    return tel[1:] if tel.startswith("0") else tel

# --- 🤖 BÖLÜM 1: AI ASİSTAN ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ondokuzmayıs Belediyesi Akıllı Asistanına hoş geldiniz. 😊 Size bugün nasıl yardımcı olabilirim?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### Hızlı İşlemler")
    r1c1, r1c2, r1c3 = st.columns(3)
    r2c1, r2c2 = st.columns(2)

    if r1c1.button("📝 Şikayet Oluştur"):
        st.session_state.messages.append({"role": "assistant", "content": "Size şikayet formuna yönlendiriyorum..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r1c2.button("🔍 Şikayet Sorgulama"):
        st.session_state.messages.append({"role": "assistant", "content": "Size kayıt sorgulama ekranına yönlendiriyorum..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r1c3.button("📩 Yazılı İşlemler"):
        st.session_state.messages.append({"role": "assistant", "content": "Size yazılı işlemler için başvuru sayfasına yönlendiriyorum..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r2c1.button("📄 Evrak & Bilgi Rehberi"):
        st.session_state.evrak_aktif = True

    if r2c2.button("📞 Belediye İletişim"):
        ans = f"📞 **Tel:** {BELEDİYE_İLETİŞİM['telefon']} \n📍 **Adres:** {BELEDİYE_İLETİŞİM['konum']}"
        st.session_state.messages.append({"role": "assistant", "content": ans}); st.rerun()

    # --- TÜM MÜDÜRLÜKLER EVRAK SORGULAMA ---
    if "evrak_aktif" in st.session_state and st.session_state.evrak_aktif:
        st.write("---")
        st.markdown("#### 📂 Evrak Sorgulama Paneli")
        m = st.selectbox("Lütfen ilgili Müdürlüğü seçiniz:", ["Seçiniz..."] + sorted(list(EVRAK_REHBERI.keys())))
        if m != "Seçiniz...":
            i = st.selectbox("Hangi işlem için evrak listesini görmek istersiniz?", ["Seçiniz..."] + list(EVRAK_REHBERI[m].keys()))
            if i != "Seçiniz...":
                belgeler = EVRAK_REHBERI[m][i]
                st.info(f"**{i}** işlemi için yanınızda bulundurmanız gereken belgeler:")
                for b in belgeler:
                    st.write(f"✅ {b}")
        if st.button("Rehberi Kapat"): del st.session_state.evrak_aktif; st.rerun()

    if prompt := st.chat_input("Mesajınızı buraya yazabilirsiniz..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        if any(x in p_low for x in ["şikayet", "yazılı", "başvuru"]):
            st.session_state.messages.append({"role": "assistant", "content": "Anlaşıldı, sizi hemen yönlendiriyorum..."})
            st.session_state.sayfa = "portal"; st.rerun()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Size şikayet kaydı, başvuru evrakları veya iletişim bilgilerimiz konusunda yardımcı olabilirim."})
            st.rerun()

# --- 📝 BÖLÜM 2: PORTAL VE 🏢 MÜDÜRLÜK PANELİ (Kodun devamı senin orijinal yapınla aynıdır) ---
elif st.session_state.sayfa == "portal":
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"; st.rerun()
    # ... (Vatandaş Portalı ve Müdürlük Paneli kodların buraya gelir)
