import streamlit as st
import pandas as pd
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide", initial_sidebar_state="collapsed")

# --- GENEL MAIL GÖNDERME FONKSİYONU ---
def mail_gonder(alici_mail, sikayet_id, konu_tipi, detay_mesaj=""):
    gonderici_mail = "SENIN_MAIL_ADRESIN@gmail.com" # Gmail adresini buraya yaz
    gonderici_sifre = "XXXX XXXX XXXX XXXX" # 16 haneli Uygulama Şifresini buraya yaz
    
    if konu_tipi == "YENI_KAYIT":
        konu = f"Şikayet Talebiniz Alındı - ID: {sikayet_id}"
        mesaj_metni = f"Sayın Vatandaşımız,\n\nŞikayet talebiniz başarıyla sisteme alınmıştır.\nTakip Numaranız: {sikayet_id}\n\nBaşvurunuz ilgili müdürlük tarafından en kısa sürede incelenecektir."
    else:
        konu = f"Şikayetiniz Güncellendi - ID: {sikayet_id}"
        mesaj_metni = f"Sayın Vatandaşımız,\n\n{sikayet_id} numaralı şikayetiniz güncellenmiştir.\n\n{detay_mesaj}\n\nSüreci portalımız üzerinden takip edebilirsiniz."

    try:
        msg = MIMEMultipart()
        msg['From'] = gonderici_mail
        msg['To'] = alici_mail
        msg['Subject'] = konu
        msg.attach(MIMEText(mesaj_metni, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gonderici_mail, gonderici_sifre)
        server.sendmail(gonderici_mail, alici_mail, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

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

# --- MÜDÜRLÜK VERİLERİ ---
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Altyapı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "İşgal", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi", "Ödeme", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + ["Emlak ve İstimlak", "Temizlik İşleri"])))

st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

# --- TAB 1: YENİ ŞİKAYET (Kayıt Anında Mail) ---
with tab1:
    st.header("Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız")
        eposta = st.text_input("E-posta Adresiniz")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
        is_email_valid = re.match(email_pattern, eposta, re.IGNORECASE) if eposta else False
        if eposta and not is_email_valid: st.warning("⚠️ Lütfen geçerli bir e-posta giriniz!")

    with c2: 
        soyad = st.text_input("Soyadınız")
        telefon_input = st.text_input("Telefon Numaranız")
    
    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler)
    detay = st.text_area("Şikayet Detayı")
    
    if st.button("Şikayeti Kaydet"):
        if ad and soyad and eposta and is_email_valid:
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            # CSV Kayıt Mantığı (Özetlendi)
            yeni_kayit = {"ID": sikayet_id, "E-posta": eposta, "Durum": "İnceleniyor", "Müdürlük": secilen_mudurluk}
            pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            
            # --- KAYIT MAİLİ GÖNDER ---
            if mail_gonder(eposta, sikayet_id, "YENI_KAYIT"):
                st.success(f"✅ Şikayetiniz alındı ve {eposta} adresine onay maili gönderildi.")
            else:
                st.success(f"✅ Şikayetiniz alındı (Mail gönderilemedi). Takip ID: {sikayet_id}")
            st.balloons()
        else:
            st.error("Lütfen formu eksiksiz ve doğru doldurunuz.")

# --- MÜDÜRLÜK PANELİ (Durum Değiştiğinde Mail) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "1234":
        df = veri_yukle()
        if not df.empty:
            secilen_id = st.selectbox("ID Seçiniz:", df["ID"].tolist())
            yeni_durum = st.selectbox("Durum:", ["İşleme Alındı", "Tamamlandı", "Reddedildi"])
            cevap = st.text_area("Cevap Notu:")
            
            if st.button("Güncelle ve Vatandaşa Bildir"):
                idx = df[df["ID"] == secilen_id].index
                hedef_mail = df.at[idx[0], "E-posta"]
                
                # CSV Güncelle
                df.at[idx[0], "Durum"] = yeni_durum
                df.at[idx[0], "Belediye_Cevabi"] = cevap
                df.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                
                # --- GÜNCELLEME MAİLİ GÖNDER ---
                detay_metni = f"Yeni Durum: {yeni_durum}\nCevap: {cevap}"
                mail_gonder(hedef_mail, secilen_id, "GUNCELLEME", detay_metni)
                st.success("İşlem tamamlandı, vatandaşa mail iletildi.")
                st.rerun()
