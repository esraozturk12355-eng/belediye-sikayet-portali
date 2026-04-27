import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide")

# 2. ÜST BAŞLIK VE LOGO
st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

# 3. MÜDÜRLÜK LİSTESİ
mudurlukler = [
    "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
    "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
]

# 4. YAN MENÜ (SIDEBAR)
menu = st.sidebar.radio("İşlem Seçiniz", ["Yeni Şikayet Oluştur", "Şikayetlerimi Görüntüle"])

if menu == "Yeni Şikayet Oluştur":
    st.header("📝 Yeni Şikayet Formu")

    col1, col2 = st.columns(2)
    with col1:
        ad = st.text_input("Adınız")
        eposta = st.text_input("E-posta Adresiniz")
    with col2:
        soyad = st.text_input("Soyadınız")
        telefon = st.text_input("Telefon Numaranız (10-11 haneli)")

    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", mudurlukler)

    sikayet_turleri_dict = {
        "Yazı İşleri Müdürlüğü": ["Evrak işlemlerinin yavaş ilerlemesi", "Bilgi eksikliği", "Diğer"],
        "Veteriner İşleri Müdürlüğü": ["Sokak hayvanlarının fazlalığı", "Yaralı hayvan", "Aşılama talebi", "Diğer"],
        "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Altyapı sorunu", "Diğer"],
        "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Kaçak satış", "Diğer"],
    }

    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi)
    adres = st.text_area("Adres Bilgisi")
    detay_metni = st.text_area("Şikayet Detayı")

    if st.button("Şikayeti Kaydet"):
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", eposta):
            st.error("Lütfen geçerli bir e-posta giriniz!")
        elif not re.match(r"^\d{10,11}$", telefon):
            st.error("Lütfen geçerli bir telefon giriniz!")
        elif not ad or not soyad:
            st.error("Lütfen ad ve soyad giriniz!")
        else:
            simdi = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            yeni_kayit = {
                "Tarih": simdi,
                "Ad": ad,
                "Soyad": soyad,
                "E-posta": eposta,
                "Telefon": telefon,
                "Müdürlük": secilen_mudurluk,
                "Tür": sikayet_turu,
                "Detay": detay_metni,
                "Adres": adres,
                "Durum": "İnceleniyor"
            }
            
            df_yeni = pd.DataFrame([yeni_kayit])
            # Kayıt esnasında utf-8-sig kullanarak Excel uyumluluğunu artırıyoruz
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            
            st.success(f"Şikayetiniz {simdi} itibarıyla başarıyla kaydedildi!")

elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")

    if arama:
        if os.path.exists("sikayetler.csv"):
            # Bozuk satırları atlaması için on_bad_lines ekledik
            df_tumu = pd.read_csv("sikayetler.csv", on_bad_lines='skip')
            df_tumu = df_tumu.sort_values(by="Tarih", ascending=False)
            
            sonuclar = df_tumu[(df_tumu["E-posta"] == arama) | (df_tumu["Telefon"].astype(str) == arama)]
            
            if not sonuclar.empty:
                st.write(f"Toplam {len(sonuclar)} adet kaydınız bulundu:")
                st.table(sonuclar[["Tarih", "Müdürlük", "Tür", "Durum", "Detay"]])
            else:
                st.warning("Kayıt bulunamadı.")
        else:
            st.info("Sistemde henüz kayıt bulunmuyor.")

# 5. MÜDÜRLÜK YÖNETİM PANELİ
st.divider() 
st.subheader("🏢 Müdürlük Yönetim Paneli")

col_admin1, col_admin2 = st.columns(2)
with col_admin1:
    admin_mudur = st.selectbox("Müdürlük Seçin:", mudurlukler, key="admin_secim")
with col_admin2:
    sifre = st.text_input("Giriş Şifresi:", type="password", key="admin_sifre")

DOGRU_SIFRE = "1234" 

if st.button("Müdürlük Kayıtlarını Listele"):
    if sifre == DOGRU_SIFRE:
        if not os.path.exists("sikayetler.csv"):
            st.warning("Henüz şikayet dosyası oluşmamış.")
        else:
            # Buraya da on_bad_lines ekledik
            df_admin = pd.read_csv("sikayetler.csv", on_bad_lines='skip')
            df_admin = df_admin.sort_values(by="Tarih", ascending=False)
            
            filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur]
            
            if not filtreli.empty:
                st.success(f"{admin_mudur} - Toplam {len(filtreli)} şikayet:")
                st.dataframe(filtreli)
            else:
                st.info(f"{admin_mudur} için henüz bir kayıt bulunmuyor.")
    else:
        st.error("Hatalı şifre!")
