import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi", 
    layout="wide",
    initial_sidebar_state="collapsed" # Varsayılan olarak kapalı tutar
)

# 2. ÜST BAŞLIK VE LOGO
st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

# --- MÜDÜRLÜKLER VE ÖZEL TÜRLER ---
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemlerinin yavaş ilerlemesi", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanlarının fazlalığı", "Yaralı hayvan", "Aşılama talebi", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Altyapı sorunu", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Kaçak satış", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı bildirimi", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu sorgulama", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + [
    "Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", 
    "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"
])))

def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"):
        return tel[1:]
    return tel

# --- SIDEBAR'I DEVRE DIŞI BIRAKIP ÜST MENÜ YAPTIK ---
# Bu sayede o oklarla uğraşmana gerek kalmaz.
tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

# --- TAB 1: YENİ ŞİKAYET ---
with tab1:
    st.header("Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız", key="ad_input")
        eposta = st.text_input("E-posta Adresiniz", key="mail_input")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
        is_email_valid = False
        if eposta != "": 
            if re.match(email_pattern, eposta, re.IGNORECASE):
                st.success("E-posta formatı geçerli. ✅")
                is_email_valid = True
            else:
                st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")
                is_email_valid = False

    with c2: 
        soyad = st.text_input("Soyadınız", key="soyad_input")
        telefon_input = st.text_input("Telefon Numaranız", key="tel_input")
    
    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_sec")
    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi, key="tur_sec")
    detay = st.text_area("Şikayet Detayı", key="detay_sec")
    
    if st.button("Şikayeti Kaydet"):
        if not (ad and soyad and eposta and telefon_input):
            st.error("Lütfen tüm alanları doldurunuz.")
        elif not is_email_valid:
            st.error("Hatalı e-posta adresi ile kayıt yapılamaz!")
        else:
            temiz_tel = tel_temizle(telefon_input)
            df_mevcut = veri_yukle()
            yeni_sira_no = 1
            if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns and "Sıra_No" in df_mevcut.columns:
                birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                if not birim_kayitlari.empty:
                    yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
            
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            yeni_kayit = {
                "ID": sikayet_id, "Sıra_No": yeni_sira_no, 
                "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu,
                "Detay": detay.replace(",", " "), "Durum": "İnceleniyor",
                "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"✅ Şikayetiniz başarıyla alınmıştır. ID: {sikayet_id}")
            st.balloons()

# --- TAB 2: ŞİKAYET GÖRÜNTÜLEME ---
with tab2:
    st.header("Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz", key="sorgu_input")
    if arama:
        temiz_arama = tel_temizle(arama)
        df = veri_yukle()
        if not df.empty:
            df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
            if not sonuclar.empty:
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else:
                st.warning("⚠️ Kayıt bulunamadı.")

# --- MÜDÜRLÜK PANELİ (Sayfanın En Altında Gizli) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1:
        admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2:
        sifre = st.text_input("Şifre:", type="password", key="adm_pass")

    if sifre == "1234":
        df_admin = veri_yukle()
        if not df_admin.empty:
            filtreli = df_admin[df_admin["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
            if not filtreli.empty:
                st.dataframe(filtreli)
                secilen_id = st.selectbox("İşlem Yapılacak ID:", filtreli["ID"].tolist())
                yeni_durum = st.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi"])
                cevap = st.text_area("Cevap Notu:")
                if st.button("Güncelle"):
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    df_admin.at[idx[0], "Durum"] = yeni_durum
                    df_admin.at[idx[0], "Belediye_Cevabi"] = cevap
                    df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                    st.success("Güncellendi!")
                    st.rerun()
