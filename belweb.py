import streamlit as st
import pandas as pd
import os
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- MAİL GÖNDERME FONKSİYONU ---
def gercek_mail_gonder(alici_mail, ad, soyad, durum, mudurluk):
    # BURAYI KENDİ BİLGİLERİNLE DOLDURMALISIN
    gonderici_mail = "senin_mailin@gmail.com" # Kendi Gmail adresin
    uygulama_sifresi = "xxxx xxxx xxxx xxxx" # Google'dan aldığın 16 haneli uygulama şifresi
    
    mesaj_metni = f"""
    Sayın {ad} {soyad},
    
    {mudurluk} birimine iletmiş olduğunuz şikayetinizin durumu güncellenmiştir.
    
    Güncel Durum: {durum}
    İşlem Tarihi: {(datetime.now() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')}
    
    Ondokuzmayıs Belediyesi Şikayet Yönetim Sistemi
    """
    
    mesaj = MIMEText(mesaj_metni)
    mesaj["Subject"] = "Belediye Şikayet Durum Güncellemesi"
    mesaj["From"] = gonderici_mail
    mesaj["To"] = alici_mail

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gonderici_mail, uygulama_sifresi)
            server.sendmail(gonderici_mail, alici_mail, mesaj.as_string())
        return True
    except Exception as e:
        st.error(f"Mail gönderilirken hata oluştu: {e}")
        return False

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide")

# 2. ÜST BAŞLIK
st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

mudurlukler = [
    "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
    "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
]

# 3. YAN MENÜ
menu = st.sidebar.radio("İşlem Seçiniz", ["Yeni Şikayet Oluştur", "Şikayetlerimi Görüntüle"])

if menu == "Yeni Şikayet Oluştur":
    st.header("📝 Yeni Şikayet Formu")
    col1, col2 = st.columns(2)
    with col1:
        ad = st.text_input("Adınız")
        eposta = st.text_input("E-posta Adresiniz")
    with col2:
        soyad = st.text_input("Soyadınız")
        telefon = st.text_input("Telefon Numaranız")

    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", mudurlukler)
    detay_metni = st.text_area("Şikayet Detayı")

    if st.button("Şikayeti Kaydet"):
        if not ad or not eposta or not telefon:
            st.error("Lütfen alanları doldurunuz!")
        else:
            simdi = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
            yeni_kayit = {
                "ID": str(datetime.now().timestamp()).split(".")[0],
                "Tarih": simdi,
                "Ad": ad,
                "Soyad": soyad,
                "E-posta": eposta,
                "Telefon": telefon,
                "Müdürlük": secilen_mudurluk,
                "Detay": detay_metni,
                "Durum": "İnceleniyor"
            }
            df_yeni = pd.DataFrame([yeni_kayit])
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            
            st.success("Şikayetiniz kaydedildi! (Gerçek mail gönderimi müdürlük panelinden yapılır.)")

elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon giriniz")
    if arama and os.path.exists("sikayetler.csv"):
        df_tumu = pd.read_csv("sikayetler.csv", on_bad_lines='skip')
        sonuclar = df_tumu[(df_tumu["E-posta"] == arama) | (df_tumu["Telefon"].astype(str) == arama)]
        if not sonuclar.empty:
            st.table(sonuclar[["Tarih", "Müdürlük", "Detay", "Durum"]])
        else:
            st.warning("Kayıt bulunamadı.")

# 4. MÜDÜRLÜK YÖNETİM PANELİ
st.divider()
st.subheader("🏢 Müdürlük Yönetim Paneli")
col_a, col_b = st.columns(2)
with col_a:
    admin_mudur = st.selectbox("Müdürlük Seçin:", mudurlukler, key="adm")
with col_b:
    sifre = st.text_input("Şifre:", type="password")

if sifre == "1234":
    if os.path.exists("sikayetler.csv"):
        df_admin = pd.read_csv("sikayetler.csv", on_bad_lines='skip')
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur].copy()
        
        if not filtreli.empty:
            st.dataframe(filtreli)
            
            if "ID" in filtreli.columns:
                st.write("---")
                st.write("🔧 **Şikayet Durumu Güncelle**")
                sikayet_id = st.selectbox("Güncellenecek Şikayet ID'sini Seçin:", filtreli["ID"].tolist())
                yeni_durum = st.selectbox("Yeni Durum:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı"])
                
                if st.button("Durumu Güncelle ve Gerçek Mail Gönder"):
                    # Veritabanını güncelle
                    df_admin.loc[df_admin["ID"].astype(str) == str(sikayet_id), "Durum"] = yeni_durum
                    df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                    
                    # Kullanıcı bilgilerini çek ve mail gönder
                    kisi_verisi = df_admin[df_admin["ID"].astype(str) == str(sikayet_id)].iloc[0]
                    mail_sonuc = gercek_mail_gonder(
                        kisi_verisi["E-posta"], 
                        kisi_verisi["Ad"], 
                        kisi_verisi["Soyad"], 
                        yeni_durum, 
                        kisi_verisi["Müdürlük"]
                    )
                    
                    if mail_sonuc:
                        st.balloons()
                        st.success(f"Durum '{yeni_durum}' yapıldı ve {kisi_verisi['E-posta']} adresine mail gönderildi!")
                    else:
                        st.warning("Durum güncellendi ama mail gönderilemedi (Ayarlarınızı kontrol edin).")
        else:
            st.info("Bu birimde şikayet yok.")
