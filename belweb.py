import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide")

st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

mudurlukler = [
    "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
    "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
]

# --- GÜVENLİ VERİ YÜKLEME FONKSİYONU ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            df = pd.read_csv("sikayetler.csv", dtype={'ID': str}, on_bad_lines='skip', index_col=False)
            # Eğer ID sütunu eksikse, hata vermemesi için boş döner veya sütunu ekler
            if "ID" not in df.columns:
                st.warning("⚠️ Veri yapısı güncel değil. Lütfen sikayetler.csv dosyasını silip yeniden başlatın.")
                return pd.DataFrame()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

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
    sikayet_turu = st.selectbox("Şikayet Türü", ["Genel Şikayet", "Bilgi Edinme", "Arıza", "Diğer"])
    adres = st.text_area("Adres Bilgisi")
    detay_metni = st.text_area("Şikayet Detayı")

    if st.button("Şikayeti Kaydet"):
        if ad and soyad and eposta:
            simdi = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
            # Benzersiz ID oluşturma
            yeni_id = str(datetime.now().timestamp()).replace(".", "")[-8:]
            
            yeni_kayit = {
                "ID": yeni_id,
                "Tarih": simdi,
                "Ad": ad,
                "Soyad": soyad,
                "E-posta": eposta,
                "Telefon": telefon,
                "Müdürlük": secilen_mudurluk,
                "Tür": sikayet_turu,
                "Detay": detay_metni,
                "Adres": adres,
                "Durum": "İnceleniyor",
                "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            
            df_yeni = pd.DataFrame([yeni_kayit])
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            st.success(f"Şikayetiniz başarıyla kaydedildi! Kayıt No: {yeni_id}")
        else:
            st.error("Lütfen gerekli alanları doldurun.")

elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon giriniz")
    if arama:
        df_tumu = veri_yukle()
        if not df_tumu.empty:
            sonuclar = df_tumu[(df_tumu["E-posta"] == arama) | (df_tumu["Telefon"].astype(str) == arama)]
            if not sonuclar.empty:
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else:
                st.warning("Kayıt bulunamadı.")

# 5. MÜDÜRLÜK YÖNETİM PANELİ
st.divider()
st.subheader("🏢 Müdürlük Yönetim Paneli")
c1, c2 = st.columns(2)
with c1:
    admin_mudur = st.selectbox("Müdürlük:", mudurlukler)
with c2:
    sifre = st.text_input("Şifre:", type="password")

if sifre == "1234":
    df_admin = veri_yukle()
    if not df_admin.empty:
        # Hata aldığın satır burasıydı, artık güvenli filtreleniyor
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur]
        if not filtreli.empty:
            st.dataframe(filtreli)
            st.write("---")
            # ID listesini güvenli alıyoruz
            id_listesi = filtreli["ID"].astype(str).tolist()
            secilen_id = st.selectbox("İşlem Yapılacak ID:", id_listesi)
            
            cevap = st.text_area("Cevabınız:")
            if st.button("Güncelle"):
                # Ana
