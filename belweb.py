import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- SESSION STATE (Sayfa Yönetimi İçin) ---
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "asistan"

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 6]) 
with c1:
    logo_dosyasi = "logo.jfif"
    if os.path.exists(logo_dosyasi):
        st.image(logo_dosyasi, width=120)
    else:
        st.write("# 🏛️") 

with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Yapay Zeka Destekli Vatandaş Portalı")

# --- VERİ YÜKLEME FONKSİYONU ---
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

# MÜDÜRLÜKLER VE BİLGİLER
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + [
    "Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", 
    "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"
])))

st.divider()

# --- 🤖 1. SAYFA: AKILLI ASİSTAN (ANA EKRAN) ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    st.write("Merhaba! Size nasıl yardımcı olabilirim? Lütfen yapmak istediğiniz işlemi seçiniz:")
    
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    if col1.button("📝 Talep ve Öneri Bildir", use_container_width=True):
        st.session_state.sayfa = "talep_ekrani"
        st.rerun()
    
    if col2.button("🔍 Talep Sorgulama", use_container_width=True):
        st.session_state.sayfa = "sorgu_ekrani"
        st.rerun()
    
    if col3.button("📄 Evrak Bilgisi", use_container_width=True):
        st.info("📄 Genel işlemler için Kimlik Fotokopisi ve Dilekçe gereklidir. Özel ruhsat işlemleri için ilgili müdürlüğe başvurunuz.")
    
    if col4.button("🏢 Müdürlük İletişim", use_container_width=True):
        st.warning("🏛️ Belediyemizde 10 aktif müdürlük hafta içi 08:30-17:30 arası hizmet vermektedir.")
        
    if col5.button("📞 İletişim", use_container_width=True):
        st.success("📞 Telefon: 0 (362) 511 44 88 \n📍 Adres: Pazar Mah. Atatürk Bulvarı No:165")

# --- 📝 2. SAYFA: TALEP VE ÖNERİ FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Talep ve Öneri Bildirim Formu")
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"
        st.rerun()
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız")
            eposta = st.text_input("E-posta Adresiniz")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = bool(re.match(email_pattern, eposta, re.IGNORECASE)) if eposta else False
        with c2: 
            soyad = st.text_input("Soyadınız")
            telefon_input = st.text_input("Telefon Numaranız")
        
        secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler)
        tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
        sikayet_turu = st.selectbox("Tür", tur_listesi)
        detay = st.text_area("Detaylı Açıklama")
        
        if st.button("Kaydet ve Gönder"):
            if ad and soyad and eposta and is_email_valid and telefon_input:
                df_mevcut = veri_yukle()
                yeni_sira_no = 1
                if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns and "Sıra_No" in df_mevcut.columns:
                    birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                    if not birim_kayitlari.empty: yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
                
                sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni_kayit = {
                    "ID": sikayet_id, "Sıra_No": yeni_sira_no, 
                    "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(telefon_input),
                    "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu,
                    "Detay": detay.replace(",", " "), "Durum": "İnceleniyor",
                    "Belediye_Cevabi": "Henüz cevaplanmadı"
                }
                pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"✅ Talebiniz alınmıştır. Takip ID: {sikayet_id}")
                st.balloons()
            else:
                st.error("Lütfen tüm alanları doğru formatta doldurunuz.")

# --- 🔍 3. SAYFA: SORGULAMA EKRANI ---
elif st.session_state.sayfa == "sorgu_ekrani":
    st.markdown("### 🔍 Talep Sorgulama")
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"
        st.rerun()
    
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
    if arama:
        df = veri_yukle()
        if not df.empty:
            df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == tel_temizle(arama))]
            if not sonuclar.empty:
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else:
                st.warning("⚠️ Kayıt bulunamadı.")

# --- 🏢 MÜDÜRLÜK PANELİ (HER ZAMAN ALTTA GİZLİ) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim:", tum_birimler, key="adm_birim")
    with cp2: sifre = st.text_input("Şifre:", type="password", key="adm_pass")

    if sifre == "1234":
        df_admin = veri_yukle()
        if not df_admin.empty:
            filtreli = df_admin[df_admin["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
            if not filtreli.empty:
                st.dataframe(filtreli)
                secilen_id = st.selectbox("İşlem Yapılacak ID:", filtreli["ID"].tolist())
                yeni_durum = st.selectbox("Durum:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"])
                cevap_notu = st.text_area("Cevap Notu:")
                if st.button("Güncellemeyi Onayla"):
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    df_admin.at[idx[0], "Durum"] = yeni_durum
                    df_admin.at[idx[0], "Belediye_Cevabi"] = cevap_notu
                    df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                    st.success("Güncellendi!")
                    st.rerun()
