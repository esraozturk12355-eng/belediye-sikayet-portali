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

mudurlukler = [
    "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
    "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
]

# --- VERİ YÜKLEME FONKSİYONU (BOZUK SATIRLARI ATLAR) ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            # on_bad_lines='skip' sayesinde hatalı satırlar uygulamayı çökertmez
            df = pd.read_csv("sikayetler.csv", dtype={'ID': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

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
        if ad and eposta and telefon:
            simdi = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-8:]
            
            yeni_kayit = {
                "ID": sikayet_id,
                "Tarih": simdi,
                "Ad": ad,
                "Soyad": soyad,
                "E-posta": eposta,
                "Telefon": telefon,
                "Müdürlük": secilen_mudurluk,
                "Detay": detay_metni.replace(",", " "), # Virgül hatasını önlemek için
                "Durum": "İnceleniyor",
                "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            
            df_yeni = pd.DataFrame([yeni_kayit])
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            
            st.success(f"Başarıyla kaydedildi! ID: {sikayet_id}")
            st.rerun()
        else:
            st.error("Lütfen tüm alanları doldurun!")

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

# 4. MÜDÜRLÜK PANELİ
st.divider()
st.subheader("🏢 Müdürlük Yönetim Paneli")
c1, c2 = st.columns(2)
with c1:
    admin_mudur = st.selectbox("Müdürlük Seçin:", mudurlukler, key="adm")
with c2:
    sifre = st.text_input("Şifre:", type="password")

if sifre == "1234":
    df_admin = veri_yukle()
    if not df_admin.empty and "Müdürlük" in df_admin.columns:
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur]
        if not filtreli.empty:
            st.dataframe(filtreli)
            st.write("---")
            if "ID" in filtreli.columns:
                secilen_id = st.selectbox("İşlem Yapılacak ID:", filtreli["ID"].tolist())
                yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "Tamamlandı", "Reddedildi"])
                yonlendir = st.selectbox("Müdürlük Yönlendir:", mudurlukler, index=mudurlukler.index(admin_mudur))
                cevap = st.text_area("Cevabınız:")
                
                if st.button("Kaydet"):
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    df_admin.at[idx[0], "Durum"] = yeni_durum
                    df_admin.at[idx[0], "Müdürlük"] = yonlendir
                    df_admin.at[idx[0], "Belediye_Cevabi"] = cevap
                    df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                    st.success("Güncellendi!")
                    st.rerun()
        else:
            st.info("Kayıt yok.")
