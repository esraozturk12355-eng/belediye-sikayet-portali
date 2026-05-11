import streamlit as st
import pandas as pd
import os
import re
import base64
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi, etiket="İndir"):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Kimden", "Birim_Dosya"]
    if os.path.exists("mesajlar.csv"):
        try: 
            df = pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
            for col in cols:
                if col not in df.columns: df[col] = "Yok"
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def tel_temizle(tel):
    tel = str(tel).strip()
    return tel[1:] if tel.startswith("0") else tel

tum_birimler = ["Destek Hizmetleri", "Emlak ve İstimlak", "Fen İşleri", "Mali Hizmetler", "Veteriner İşleri", "Yapı Kontrol", "Yazı İşleri", "Zabıta", "İklim Değişikliği ve Sıfır Atık", "İmar ve Şehircilik"]

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Gelişmiş Vatandaş İletişim Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📝 Talep/Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("📄 Evrak Bilgisi"): st.info("Gerekli evraklar için müdürlükle iletişime geçiniz.")
    if col4.button("📞 İletişim"): st.info("📞 0 (362) 511 44 88")

# --- 📝 2. SAYFA: TALEP FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("talep"):
        ad, soyad = st.columns(2)
        v_ad = ad.text_input("Ad")
        v_soyad = soyad.text_input("Soyad")
        v_mail = st.text_input("E-posta")
        v_mud = st.selectbox("Müdürlük", tum_birimler)
        v_detay = st.text_area("Açıklama")
        if st.form_submit_button("Gönder"):
            sid = str(datetime.now().timestamp()).replace(".","")[-6:]
            yeni = {"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": v_ad, "Soyad": v_soyad, "E-posta": v_mail, "Müdürlük": v_mud, "Detay": v_detay, "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
            pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"Talebiniz Alındı! ID: {sid}")

# --- 🔍 3. SAYFA: SORGULAMA VE SOHBET ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    c_mail = st.text_input("E-posta Adresiniz:")
    c_sifre = st.text_input("Sohbet Şifreniz:", type="password")
    
    if c_mail and c_sifre:
        df_m = mesaj_yukle()
        # Kullanıcıya özel sohbet geçmişini filtrele
        sohbet_gecmisi = df_m[(df_m["Gonderen"] == c_mail) & (df_m["Sifre"].astype(str) == str(c_sifre))]
        
        st.markdown(f"#### 💬 {c_mail} - Sohbet Geçmişi")
        for _, msg in sohbet_gecmisi.iterrows():
            rol = "user" if msg["Kimden"] == "Vatandaş" else "assistant"
            with st.chat_message(rol):
                st.write(f"**{msg['Kimden']} ({msg['Tarih']}):** {msg['Mesaj']}")
                if msg["Dosya_Adi"] != "Yok":
                    yol = "yuklenen_belgeler" if msg["Kimden"] == "Vatandaş" else "belediye_belgeleri"
                    full_yol = os.path.join(yol, str(msg["Dosya_Adi"]))
                    if os.path.exists(full_yol):
                        with open(full_yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(msg["Dosya_Adi"])), unsafe_allow_html=True)

        st.divider()
        with st.form("yeni_mesaj_form"):
            yeni_m = st.text_area("Mesajınızı yazın:")
            yeni_f = st.file_uploader("Dosya Ekle:")
            yeni_mud = st.selectbox("Hangi Birime?", tum_birimler) if sohbet_gecmisi.empty else st.hidden()
            if st.form_submit_button("Gönder"):
                d_adi = "Yok"
                if yeni_f:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    d_adi = f"{datetime.now().strftime('%H%M%S')}_{yeni_f.name}"
                    with open(os.path.join("yuklenen_belgeler", d_adi), "wb") as f: f.write(yeni_f.getbuffer())
                
                hedef_mud = yeni_mud if sohbet_gecmisi.empty else sohbet_gecmisi.iloc[0]["Mudurluk"]
                yeni_row = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": c_mail, "Sifre": str(c_sifre), "Mudurluk": hedef_mud, "Mesaj": yeni_m, "Dosya_Adi": d_adi, "Kimden": "Vatandaş", "Birim_Dosya": "Yok"}
                pd.DataFrame([yeni_row]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.rerun()

# --- 🏢 MÜDÜRLÜK PANELİ ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    a_birim = st.selectbox("Birim:", tum_birimler)
    a_sifre = st.text_input("Şifre:", type="password")
    if a_sifre == "1234":
        df_all = mesaj_yukle()
        birim_mesajlari = df_all[df_all["Mudurluk"] == a_birim]
        
        # Benzersiz kullanıcıları (sohbetleri) listele
        farkli_kullanicilar = birim_mesajlari["Gonderen"].unique()
        
        if len(farkli_kullanicilar) > 0:
            secilen_user = st.selectbox("Sohbet Seçin (Vatandaş E-postası):", farkli_kullanicilar)
            user_sohbet = birim_mesajlari[birim_mesajlari["Gonderen"] == secilen_user]
            
            for _, m in user_sohbet.iterrows():
                with st.chat_message("user" if m["Kimden"] == "Vatandaş" else "assistant"):
                    st.write(f"**{m['Kimden']} ({m['Tarih']}):** {m['Mesaj']}")
                    if m["Dosya_Adi"] != "Yok":
                        yol = "yuklenen_belgeler" if m["Kimden"] == "Vatandaş" else "belediye_belgeleri"
                        if os.path.exists(os.path.join(yol, str(m["Dosya_Adi"]))):
                            with open(os.path.join(yol, str(m["Dosya_Adi"])), "rb") as f:
                                st.markdown(dosya_indirme_linki(f.read(), str(m["Dosya_Adi"])), unsafe_allow_html=True)
            
            with st.form("admin_cevap"):
                adm_m = st.text_area("Cevabınız:")
                adm_f = st.file_uploader("Belge Gönder:")
                if st.form_submit_button("Vatandaşa Gönder"):
                    d_adi = "Yok"
                    if adm_f:
                        if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                        d_adi = f"belediye_{datetime.now().strftime('%H%M')}_{adm_f.name}"
                        with open(os.path.join("belediye_belgeleri", d_adi), "wb") as f: f.write(adm_f.getbuffer())
                    
                    yeni_cevap = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": secilen_user, "Sifre": user_sohbet.iloc[0]["Sifre"], "Mudurluk": a_birim, "Mesaj": adm_m, "Dosya_Adi": d_adi, "Kimden": "Müdürlük", "Birim_Dosya": "Yok"}
                    pd.DataFrame([yeni_cevap]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                    st.success("Mesaj gönderildi!"); st.rerun()
        else: st.info("Bu birime henüz bir mesaj gelmemiş.")
