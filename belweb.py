import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="wide")

st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

# MÜDÜRLÜKLER VE ÖZEL TÜRLER (Ek Sorular)
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemlerinin yavaş ilerlemesi", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanlarının fazlalığı", "Yaralı hayvan", "Aşılama talebi", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Altyapı sorunu", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Kaçak satış", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı bildirimi", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu sorgulama", "Ödeme problemleri", "Diğer"]
}
# Listeyi oluştur ve alfabetik sırala
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + [
    "Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", 
    "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"
])))

def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# 4. YAN MENÜ (SIDEBAR) - İSİMLER GÜNCELLENDİ
menu = st.sidebar.radio("İşlem Seçiniz", ["Yeni Şikayet Oluştur", "Şikayetlerimi Görüntüle"])

# --- YENİ ŞİKAYET OLUŞTURMA ---
if menu == "Yeni Şikayet Oluştur":
    st.header("📝 Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız")
        eposta = st.text_input("E-posta Adresiniz")
    with c2:
        soyad = st.text_input("Soyadınız")
        telefon = st.text_input("Telefon Numaranız")
    
    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler)
    
    # Seçilen müdürlüğe göre ek soruları (Türleri) getir
    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi)
    
    detay = st.text_area("Şikayet Detayı")
    
    if st.button("Şikayeti Kaydet"):
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
            
            # Başarı mesajı ekranda kalır
            st.success(f"✅ Şikayetiniz başarıyla kaydedildi! Takip No (ID): {sikayet_id}")
            st.balloons()
        else:
            st.error("Lütfen Ad, Soyad ve E-posta alanlarını boş bırakmayınız.")

# --- ŞİKAYET GÖRÜNTÜLEME ---
elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
    if arama:
        df = veri_yukle()
        if not df.empty:
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon"].astype(str) == arama)]
            if not sonuclar.empty:
                st.info(f"Toplam {len(sonuclar)} adet kaydınız bulundu:")
                st.table(sonuclar[["Tarih", "Müdürlük", "Tür", "Durum", "Belediye_Cevabi"]])
            else:
                st.warning("Bu bilgilere ait bir kayıt bulunamadı.")

# --- MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
st.subheader("🏢 Müdürlük Yönetim Paneli")
cp1, cp2 = st.columns(2)
with cp1:
    admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
with cp2:
    sifre = st.text_input("Giriş Şifresi:", type="password")

if sifre == "1234":
    df_admin = veri_yukle()
    if not df_admin.empty:
        filtreli = df_admin[df_admin["Müdürlük"] == admin_birim]
        if not filtreli.empty:
            st.write(f"### {admin_birim} Şikayetleri")
            st.dataframe(filtreli)
            st.write("---")
            
            # Düzenleme Alanı
            with st.container():
                id_listesi = filtreli["ID"].astype(str).tolist()
                secilen_id = st.selectbox("İşlem Yapılacak ID'yi Seçin:", id_listesi)
                
                ci1, ci2 = st.columns(2)
                with ci1:
                    yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"])
                    yönlendir = st.selectbox("Müdürlük Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim))
                with ci2:
                    cevap = st.text_area("Vatandaşa Cevap Yazın:")
                
                if st.button("Değişiklikleri Onayla"):
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    if not idx.empty:
                        df_admin.at[idx[0], "Durum"] = yeni_durum
                        df_admin.at[idx[0], "Müdürlük"] = yönlendir
                        df_admin.at[idx[0], "Belediye_Cevabi"] = cevap
                        df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.success("İşlem kaydedildi!")
                        st.rerun()
        else:
            st.info(f"{admin_birim} birimi için kayıt bulunmuyor.")
    else:
        st.error("Veritabanında henüz kayıtlı şikayet yok.")
