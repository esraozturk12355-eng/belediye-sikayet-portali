import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide")

st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

# MÜDÜRLÜKLER VE ÖZEL TÜRLER
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemlerinin yavaş ilerlemesi", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanlarının fazlalığı", "Yaralı hayvan", "Aşılama talebi", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Altyapı sorunu", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Kaçak satış", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı bildirimi", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu sorgulama", "Ödeme problemleri", "Diğer"]
}
mudurlukler = list(sikayet_turleri_dict.keys()) + ["Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"]
mudurlukler = sorted(list(set(mudurlukler)))

def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except:
            return pd.DataFrame()
    return pd.DataFrame()

menu = st.sidebar.radio("İşlem Seçiniz", ["Yeni Şikayet Oluştur", "Şikayetlerimi Görüntüle"])

# --- YENİ ŞİKAYET OLUŞTURMA ---
if menu == "Yeni Şikayet Oluştur":
    st.header("📝 Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız")
        eposta = st.text_input("E-posta")
    with c2:
        soyad = st.text_input("Soyadınız")
        telefon = st.text_input("Telefon")
    
    secilen_mudurluk = st.selectbox("Müdürlük", mudurlukler)
    
    # EK SORULAR (Seçilen müdürlüğe göre değişen türler)
    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi)
    
    detay = st.text_area("Şikayetiniz")
    
    if st.button("Kaydet"):
        if ad and soyad and eposta:
            simdi = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            
            yeni_kayit = {
                "ID": sikayet_id, "Tarih": simdi, "Ad": ad, "Soyad": soyad,
                "E-posta": eposta, "Telefon": telefon, "Müdürlük": secilen_mudurluk,
                "Tür": sikayet_turu, "Detay": detay.replace(",", " "), 
                "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            df_yeni = pd.DataFrame([yeni_kayit])
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            
            # Başarı mesajı
            st.success(f"✅ Şikayetiniz başarıyla kaydedildi! Takip ID: {sikayet_id}")
            st.info("Şikayetinizi 'Şikayetlerimi Görüntüle' menüsünden bu ID veya bilgilerinizle takip edebilirsiniz.")
        else:
            st.error("Lütfen tüm zorunlu alanları (Ad, Soyad, E-posta) doldurunuz.")

# --- ŞİKAYET SORGULAMA ---
elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon giriniz")
    if arama:
        df = veri_yukle()
        if not df.empty:
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon"].astype(str) == arama)]
            if not sonuclar.empty:
                st.write("Şikayetleriniz:")
                st.table(sonuclar[["Tarih", "Müdürlük", "Tür", "Durum", "Belediye_Cevabi"]])
            else:
                st.warning("Kayıt bulunamadı.")

# --- MÜDÜRLÜK PANELİ ---
st.divider()
st.subheader("🏢 Müdürlük Yönetim Paneli")
cp1, cp2 = st.columns(2)
with cp1:
    admin_mudur = st.selectbox("Biriminiz:", mudurlukler, key="admin_birim")
with cp2:
    sifre = st.text_input("Şifre:", type="password")

if sifre == "1234":
    df_admin = veri_yukle()
    if not df_admin.empty:
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur]
        if not filtreli.empty:
            st.write(f"### {admin_mudur} Kayıtları")
            st.dataframe(filtreli)
            st.write("---")
            
            with st.container():
                id_listesi = filtreli["ID"].astype(str).tolist()
                secilen_id = st.selectbox("Düzenlenecek Şikayet ID'sini Seçin:", id_listesi)
                
                ci1, ci2 = st.columns(2)
                with ci1:
                    yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"])
                    yönlendir = st.selectbox("Başka Müdürlüğe Gönder:", mudurlukler, index=mudurlukler.index(admin_mudur))
                with ci2:
                    cevap = st.text_area("Vatandaşa Yazılacak Cevap:")
                
                if st.button("Değişiklikleri Kaydet"):
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    if not idx.empty:
                        df_admin.at[idx[0], "Durum"] = yeni_durum
                        df_admin.at[idx[0], "Müdürlük"] = yönlendir
                        df_admin.at[idx[0], "Belediye_Cevabi"] = cevap
                        df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.success("İşlem başarıyla tamamlandı!")
                        st.rerun()
        else:
            st.info(f"{admin_mudur} birimi için kayıt bulunmuyor.")
    else:
        st.error("Sistemde henüz kayıtlı şikayet yok.")
   
