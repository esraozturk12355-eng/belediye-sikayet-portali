import streamlit as st
import pandas as pd
import os
import re
import base64
import time
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- YARDIMCI FONKSİYONLAR ---
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net|org)$'
PHONE_PATTERN = r'^(0?)[5][0-9]{9}$'

def tr_saat():
    return (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")

def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: 
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Ad", "Soyad", "Gonderen", "Telefon", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
    if os.path.exists("mesajlar.csv"):
        try: 
            df = pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
            for col in cols:
                if col not in df.columns: df[col] = "Yok"
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"): return tel[1:]
    return tel

def dosya_indirme_linki(dosya_yolu, dosya_adi, etiket="İndir"):
    if not os.path.exists(dosya_yolu): return f"⚠️ {dosya_adi} yok"
    with open(dosya_yolu, "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold;">📩 {etiket}</a>'

# --- 📚 MÜDÜRLÜK REHBERİ ---
EVRAK_REHBERI_DICT = {
    "Yazı İşleri Müdürlüğü": {"Genel Dilekçe": ["Kimlik", "Dilekçe"]},
    "Fen İşleri Müdürlüğü": {"Yol Onarım": ["Konum", "Fotoğraf"]},
    "Zabıta Müdürlüğü": {"Ruhsat": ["Tapu", "Vergi Levhası"]},
    "İmar ve Şehircilik Müdürlüğü": {"İnşaat Ruhsatı": ["Tapu", "Proje"]},
    "Veteriner İşleri Müdürlüğü": {"İlaçlama": ["Adres"]},
    "Mali Hizmetler Müdürlüğü": {"Emlak Vergisi": ["Tapu"]},
    "Emlak ve İstimlak Müdürlüğü": {"Kiralama": ["Dilekçe"]},
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {"Geri Dönüşüm": ["Adres"]},
    "Destek Hizmetleri Müdürlüğü": {"İhale": ["Şartname"]},
    "Yapı Kontrol Müdürlüğü": {"Riskli Yapı": ["Tapu"]}
}
tum_birimler = sorted(list(EVRAK_REHBERI_DICT.keys()))

# --- SESSION STATE ---
if "portal_modu" not in st.session_state: st.session_state.portal_modu = "karşılama"
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan_ana"

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Dijital Vatandaş & Yönetim Portalı")
st.divider()

# --- 🚀 1. EKRAN: GİRİŞ SEÇİMİ ---
if st.session_state.portal_modu == "karşılama":
    st.markdown("<h2 style='text-align: center;'>Giriş Türünü Seçiniz</h2>", unsafe_allow_html=True)
    cv, cm = st.columns(2)
    with cv:
        if st.button("👤 Vatandaş Girişi", use_container_width=True):
            st.session_state.portal_modu = "vatandas"; st.rerun()
    with cm:
        if st.button("🏢 Müdürlük Girişi", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"; st.rerun()

# --- 👤 2. EKRAN: VATANDAŞ PORTALI ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Menü"): 
        st.session_state.portal_modu = "karşılama"; st.session_state.sayfa = "asistan_ana"; st.rerun()

    if st.session_state.sayfa == "asistan_ana":
        st.markdown("### 🤖 Nasıl Yardımcı Olabilirim?")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📝 Yeni Talep"): st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Takip"): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("📄 Evraklar"): st.session_state.sayfa = "evrak_rehberi"; st.rerun()
        if c4.button("💬 Sohbet"): st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("talep_form"):
            ad = st.text_input("Ad"); soyad = st.text_input("Soyad")
            ep = st.text_input("E-posta"); tel = st.text_input("Telefon")
            mud = st.selectbox("Müdürlük", tum_birimler)
            # BURADA SÜTUN ADINI "Açıklama" YAPTIK
            aciklama = st.text_area("Talebiniz / Açıklamanız")
            if st.form_submit_button("Gönder"):
                yeni_veri = pd.DataFrame([{
                    "ID": str(time.time()).replace(".","")[-6:], 
                    "Tarih": tr_saat(), "Ad": ad, "Soyad": soyad, 
                    "E-posta": ep, "Telefon": tel_temizle(tel), 
                    "Müdürlük": mud, "Açıklama": aciklama, # SÜTUN ADI
                    "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz yok"
                }])
                yeni_veri.to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success("✅ İletildi!"); time.sleep(1.5); st.rerun()

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Takip")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Telefon")
        if arama:
            df = veri_yukle()
            if not df.empty:
                sonuc = df[(df["E-posta"] == arama) | (df["Telefon"].apply(tel_temizle) == tel_temizle(arama))]
                st.dataframe(sonuc, use_container_width=True)

# --- 🏢 3. EKRAN: MÜDÜRLÜK PANELİ ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Menü"): st.session_state.portal_modu = "karşılama"; st.rerun()
    adm_b = st.selectbox("Biriminiz:", tum_birimler)
    adm_s = st.text_input("Şifre:", type="password")
    
    if adm_s == "1234":
        st.markdown(f"### 🏢 {adm_b} Yönetim Paneli")
        df_t = veri_yukle()
        if not df_t.empty:
            # Sadece bu müdürlüğe ait talepler
            filt = df_t[df_t["Müdürlük"] == adm_b]
            if not filt.empty:
                st.info("Aşağıdaki tabloda 'Açıklama' sütunundan vatandaşın yazdıklarını görebilirsiniz.")
                # TÜM TABLOYU GÖSTERİYORUZ (Hata almamak için sütun seçmedik)
                st.dataframe(filt, use_container_width=True)
                
                sid = st.selectbox("İşlem yapılacak ID:", filt["ID"].tolist())
                with st.container(border=True):
                    yd = st.selectbox("Yeni Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                    ans = st.text_area("Vatandaşa Yanıtınız:")
                    if st.button("Güncelle ve Kaydet"):
                        idx = df_t[df_t["ID"] == sid].index
                        df_t.at[idx[0], "Belediye_Cevabi"] = ans
                        df_t.at[idx[0], "Durum"] = yd
                        df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
            else:
                st.warning("Bu birime ait henüz talep yok.")
