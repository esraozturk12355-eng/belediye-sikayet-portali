import streamlit as st
import pandas as pd
import os
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
    detay = st.text_area("Şikayetiniz")
    
    if st.button("Kaydet"):
        if ad and soyad and eposta:
            simdi = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            
            yeni_kayit = {
                "ID": sikayet_id, "Tarih": simdi, "Ad": ad, "Soyad": soyad,
                "E-posta": eposta, "Telefon": telefon, "Müdürlük": secilen_mudurluk,
                "Detay": detay.replace(",", " "), "Durum": "İnceleniyor",
                "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            df_yeni = pd.DataFrame([yeni_kayit])
            if not os.path.exists("sikayetler.csv"):
                df_yeni.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
            else:
                df_yeni.to_csv("sikayetler.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
            st.success(f"Kaydedildi! ID: {sikayet_id}")
            st.rerun()

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
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])

# --- MÜDÜRLÜK PANELİ (DÜZENLEME GARANTİLİ) ---
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
        # Seçilen müdürlüğün kayıtlarını göster
        filtreli = df_admin[df_admin["Müdürlük"] == admin_mudur]
        
        if not filtreli.empty:
            st.write(f"### {admin_mudur} Kayıtları")
            st.dataframe(filtreli)
            
            st.write("---")
            st.info("💡 Aşağıdaki alandan şikayeti seçip cevaplayabilir veya başka birime gönderebilirsiniz.")
            
            # Düzenleme Paneli
            with st.container():
                # ID Listesini al
                id_listesi = filtreli["ID"].astype(str).tolist()
                secilen_id = st.selectbox("Düzenlenecek Şikayet ID'sini Seçin:", id_listesi)
                
                col_islem1, col_islem2 = st.columns(2)
                with col_islem1:
                    yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"])
                    yönlendir = st.selectbox("Başka Müdürlüğe Gönder:", mudurlukler, index=mudurlukler.index(admin_mudur))
                with col_islem2:
                    cevap = st.text_area("Vatandaşa Yazılacak Cevap:")
                
                if st.button("Değişiklikleri Kaydet ve Yayınla"):
                    # Ana DataFrame'de bul ve güncelle
                    idx = df_admin[df_admin["ID"] == secilen_id].index
                    if not idx.empty:
                        df_admin.at[idx[0], "Durum"] = yeni_durum
                        df_admin.at[idx[0], "Müdürlük"] = yönlendir
                        df_admin.at[idx[0], "Belediye_Cevabi"] = cevap
                        
                        df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.balloons()
                        st.success("İşlem başarıyla tamamlandı!")
                        st.rerun()
        else:
            st.warning(f"{admin_mudur} birimine ait henüz bir şikayet bulunmuyor.")
    else:
        st.error("Henüz sistemde hiç şikayet kaydı yok.")
