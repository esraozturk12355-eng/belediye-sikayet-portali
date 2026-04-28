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
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 6]) 
with c1:
    # Samsun Ondokuzmayıs Belediyesi Logosu
    st.image("https://www.19mayis.bel.tr/images/logo.png", width=100) 
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

# MÜDÜRLÜKLER
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

# --- ANA SAYFA SEKMELERİ ---
tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

# --- TAB 1: YENİ ŞİKAYET ---
with tab1:
    st.markdown("### 📝 Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız", key="ad_yeni")
        eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
        is_email_valid = False
        if eposta != "": 
            if re.match(email_pattern, eposta, re.IGNORECASE):
                st.success("E-posta formatı geçerli. ✅")
                is_email_valid = True
            else:
                st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")

    with c2: 
        soyad = st.text_input("Soyadınız", key="soyad_yeni")
        telefon_input = st.text_input("Telefon Numaranız", key="tel_yeni")
    
    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_yeni")
    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi, key="tur_yeni")
    detay = st.text_area("Şikayet Detayı", key="detay_yeni")
    
    if st.button("Şikayeti Kaydet"):
        if ad and soyad and eposta and is_email_valid and telefon_input:
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
            
            st.success(f"✅ Şikayetiniz başarıyla alınmıştır. Takip ID: {sikayet_id}")
            wp_mesaj = f"Sayın {ad} {soyad}, {sikayet_id} numaralı şikayet talebiniz Ondokuzmayıs Belediyesi tarafından alınmıştır. Teşekkür ederiz."
            link = wp_link_olustur(temiz_tel, wp_mesaj)
            st.markdown(f'''<a href="{link}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">📱 Vatandaşa WhatsApp'tan Bildir</button></a>''', unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("Lütfen formu eksiksiz ve doğru formatta doldurunuz.")

# --- TAB 2: ŞİKAYET GÖRÜNTÜLEME ---
with tab2:
    st.markdown("### 🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz", key="sorgu_input")
    if arama:
        temiz_arama = tel_temizle(arama)
        df = veri_yukle()
        if not df.empty:
            df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
            if not sonuclar.empty:
                st.info(f"Toplam {len(sonuclar)} adet kaydınız bulundu:")
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else:
                st.warning("⚠️ Bu bilgilere ait bir şikayet kaydı bulunamadı.")

# --- MÜDÜRLÜK PANELİ ---
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
                st.dataframe(filtreli[["Sıra_No", "ID", "Tarih", "Ad", "Soyad", "Telefon", "Durum", "Detay", "Belediye_Cevabi"]])
                st.write("---")
                secilen_id = st.selectbox("İşlem Yapılacak ID Seçiniz:", filtreli["ID"].tolist(), key="islem_id")
                
                ci1, ci2 = st.columns(2)
                with ci1:
                    yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"], key="durum_up")
                    yonlendir = st.selectbox("Başka Birime Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim), key="yonlendir_up")
                with ci2:
                    cevap_notu = st.text_area("Cevap Notu:", key="cevap_up")
                
                if st.button("Değişiklikleri Onayla"):
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    alici_ad = df_admin.at[idx[0], "Ad"]
                    alici_tel = df_admin.at[idx[0], "Telefon"]
                    
                    if df_admin.at[idx[0], "Müdürlük"] != yonlendir:
                        hedef = df_admin[df_admin["Müdürlük"] == yonlendir]
                        df_admin.at[idx[0], "Sıra_No"] = 1 if hedef.empty else hedef["Sıra_No"].max() + 1
                    
                    df_admin.at[idx[0], "Durum"] = yeni_durum
                    df_admin.at[idx[0], "Müdürlük"] = yonlendir
                    df_admin.at[idx[0], "Belediye_Cevabi"] = cevap_notu
                    df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                    
                    st.success("Kayıt güncellendi!")
                    guncel_mesaj = f"Sayın {alici_ad}, {secilen_id} numaralı şikayetiniz güncellenmiştir.\nYeni Durum: {yeni_durum}\nCevap: {cevap_notu}"
                    link = wp_link_olustur(alici_tel, guncel_mesaj)
                    st.markdown(f'''<a href="{link}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">📱 Güncellemeyi WhatsApp'tan Gönder</button></a>''', unsafe_allow_html=True)
                    st.rerun()
