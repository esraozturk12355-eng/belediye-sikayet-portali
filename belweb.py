import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide")

# 2. ÜST BAŞLIK
st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

# 3. MÜDÜRLÜK LİSTESİ
mudurlukler = [
    "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
    "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
]

# 4. YAN MENÜ
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
                "ID": str(datetime.now().timestamp()).split(".")[0], # Her şikayete eşsiz ID
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
            
            st.success(f"Şikayetiniz Kaydedildi. Kişinin {eposta} adresine bilgilendirme mesajı gönderildi! 📩")

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

# 5. MÜDÜRLÜK YÖNETİM PANELİ (GELİŞMİŞ)
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
        # Sadece ilgili müdürlüğün şikayetlerini filtrele
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur].copy()
        
        if not filtreli.empty:
            st.success(f"{admin_mudur} birimine ait kayıtlar:")
            st.dataframe(filtreli)
            
            # --- DURUM GÜNCELLEME KISMI ---
            st.write("---")
            st.write("🔧 **Şikayet Durumu Güncelle**")
            sikayet_id = st.selectbox("Güncellenecek Şikayet ID'sini Seçin:", filtreli["ID"].tolist())
            yeni_durum = st.selectbox("Yeni Durum:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı"])
            
            if st.button("Durumu Güncelle ve Kişiye Bildir"):
                # CSV'de ilgili satırı bul ve güncelle
                df_admin.loc[df_admin["ID"].astype(str) == str(sikayet_id), "Durum"] = yeni_durum
                df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                
                # Kişi bilgilerini al (Bildirim simülasyonu için)
                kisi = df_admin[df_admin["ID"].astype(str) == str(sikayet_id)].iloc[0]
                
                st.balloons() # Kutlama efekti
                st.success(f"Şikayet durumu '{yeni_durum}' olarak güncellendi.")
                st.info(f"📢 BİLDİRİM GÖNDERİLDİ: Sayın {kisi['Ad']} {kisi['Soyad']}, {kisi['Müdürlük']} birimine yaptığınız şikayet '{yeni_durum}' olarak işaretlenmiştir.")
        else:
            st.info("Bu birime ait şikayet bulunmuyor.")
    else:
        st.warning("Henüz veritabanı oluşmamış.")
elif sifre != "":
    st.error("Hatalı şifre.")
