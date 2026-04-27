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

def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
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
    detay_metni = st.text_area("Şikayet Detayı")

    if st.button("Şikayeti Kaydet"):
        if ad and eposta and telefon:
            simdi = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
            # Güvenli ID oluşturma
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            
            yeni_kayit = {
                "ID": sikayet_id,
                "Tarih": simdi,
                "Ad": ad,
                "Soyad": soyad,
                "E-posta": eposta,
                "Telefon": telefon,
                "Müdürlük": secilen_mudurluk,
                "Detay": detay_metni.replace(",", " "),
                "Durum": "İnceleniyor",
                "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            
            df_yeni = pd.DataFrame([yeni_kayit])
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            
            st.success(f"Kaydedildi! Takip ID: {sikayet_id}")
            st.rerun()

elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon giriniz")
    if arama:
        df_tumu = veri_yukle()
        if not df_tumu.empty:
            sonuclar = df_tumu[(df_tumu["E-posta"] == arama) | (df_tumu["Telefon"].astype(str) == arama)]
            if not sonuclar.empty:
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])

# --- MÜDÜRLÜK PANELİ (DÜZENLEME ÖZELLİKLİ) ---
st.divider()
st.subheader("🏢 Müdürlük Yönetim Paneli")
c1, c2 = st.columns(2)
with c1:
    admin_mudur = st.selectbox("Birim Seçin:", mudurlukler, key="adm_birim")
with c2:
    sifre = st.text_input("Şifre:", type="password")

if sifre == "1234":
    df_admin = veri_yukle()
    if not df_admin.empty:
        # Seçilen müdürlüğe göre filtrele
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur]
        
        if not filtreli.empty:
            st.dataframe(filtreli)
            
            if "ID" in filtreli.columns:
                st.write("---")
                st.write("### ✍️ Şikayeti Düzenle")
                
                # ID seçimi
                secilen_id = st.selectbox("İşlem Yapılacak Şikayet ID:", filtreli["ID"].tolist())
                
                col_a, col_b = st.columns(2)
                with col_a:
                    yeni_durum = st.selectbox("Durum:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"])
                    yeni_birim = st.selectbox("Müdürlük Yönlendir:", mudurlukler, index=mudurlukler.index(admin_mudur))
                with col_b:
                    cevap = st.text_area("Vatandaşa Cevap Yazın:")

                if st.button("Değişiklikleri Uygula"):
                    # Ana dosyada güncelleme yap
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    if not idx.empty:
                        df_admin.at[idx[0], "Durum"] = yeni_durum
                        df_admin.at[idx[0], "Müdürlük"] = yeni_birim
                        df_admin.at[idx[0], "Belediye_Cevabi"] = cevap
                        
                        df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.balloons()
                        st.success("Güncelleme yapıldı!")
                        st.rerun()
            else:
                st.error("Dosyada ID sütunu eksik. Lütfen sikayetler.csv dosyasını GitHub'dan silip yeni şikayet oluşturun.")
        else:
            st.info("Bu birime ait şikayet bulunamadı.")
