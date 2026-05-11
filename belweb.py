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
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Kimden"]
    if os.path.exists("mesajlar.csv"):
        try: 
            df = pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
            for col in cols:
                if col not in df.columns: df[col] = "Yok"
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

tum_birimler = ["Destek Hizmetleri", "Emlak ve İstimlak", "Fen İşleri", "Mali Hizmetler", "Veteriner İşleri", "Yapı Kontrol", "Yazı İşleri", "Zabıta", "İklim Değişikliği ve Sıfır Atık", "İmar ve Şehircilik"]

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Vatandaş İletişim ve Sohbet Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    st.write("Merhaba! Yapmak istediğiniz işlemi seçiniz:")
    col1, col2, col3 = st.columns(3)
    if col1.button("📝 Talep ve Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Talep Sorgulama"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("💬 Müdürlükle İletişime Geç (Sohbet)"): st.session_state.sayfa = "sohbet_ekrani"; st.rerun()

# --- 📝 2. SAYFA: TALEP FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Yeni Talep Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("talep"):
        v_ad = st.text_input("Ad")
        v_mail = st.text_input("E-posta")
        v_mud = st.selectbox("İlgili Birim", tum_birimler)
        v_detay = st.text_area("Açıklama")
        if st.form_submit_button("Talebi Gönder"):
            sid = str(datetime.now().timestamp()).replace(".","")[-6:]
            yeni = {"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": v_ad, "E-posta": v_mail, "Müdürlük": v_mud, "Detay": v_detay, "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
            pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"Talebiniz kaydedildi. ID: {sid}")

# --- 🔍 3. SAYFA: SORGULAMA ---
elif st.session_state.sayfa == "sorgu_ekrani":
    st.markdown("### 🔍 Başvuru Takibi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    s_mail = st.text_input("E-posta Adresiniz:")
    if s_mail:
        df_s = veri_yukle()
        if not df_s.empty:
            sonuc = df_s[df_s["E-posta"] == s_mail]
            if not sonuc.empty: st.table(sonuc[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else: st.warning("Kayıt bulunamadı.")

# --- 💬 4. SAYFA: MÜDÜRLÜK SOHBET ODASI ---
elif st.session_state.sayfa == "sohbet_ekrani":
    st.markdown("### 💬 Müdürlük Sohbet Odası")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    col_l, col_r = st.columns([1, 2])
    with col_l:
        u_mail = st.text_input("E-posta Adresiniz:")
        u_sifre = st.text_input("Sohbet Şifreniz:", type="password")
        u_mud = st.selectbox("İletişime Geçilecek Birim:", tum_birimler)
    
    if u_mail and u_sifre:
        df_m = mesaj_yukle()
        # Kullanıcının sohbet geçmişini e-posta ve şifreye göre filtrele
        sohbet = df_m[(df_m["Gonderen"] == u_mail) & (df_m["Sifre"].astype(str) == str(u_sifre))]
        
        with col_r:
            st.markdown(f"**Sohbet Geçmişi ({u_mail})**")
            chat_container = st.container(height=400)
            with chat_container:
                if sohbet.empty:
                    st.info("Henüz bir mesajlaşma bulunmuyor. İlk mesajı aşağıdan gönderebilirsiniz.")
                else:
                    for _, m in sohbet.iterrows():
                        with st.chat_message("user" if m["Kimden"] == "Vatandaş" else "assistant"):
                            st.write(f"**{m['Kimden']} ({m['Tarih']}):** {m['Mesaj']}")
                            if m["Dosya_Adi"] != "Yok":
                                yol = "yuklenen_belgeler" if m["Kimden"] == "Vatandaş" else "belediye_belgeleri"
                                if os.path.exists(os.path.join(yol, str(m["Dosya_Adi"]))):
                                    with open(os.path.join(yol, str(m["Dosya_Adi"])), "rb") as f:
                                        st.markdown(dosya_indirme_linki(f.read(), str(m["Dosya_Adi"])), unsafe_allow_html=True)
            
            # Mesaj Gönderme Alanı
            with st.form("chat_form", clear_on_submit=True):
                msg_input = st.text_area("Mesajınızı yazın:")
                file_input = st.file_uploader("Dosya Ekle (Opsiyonel):")
                if st.form_submit_button("Gönder"):
                    if msg_input:
                        f_adi = "Yok"
                        if file_input:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            f_adi = f"{datetime.now().strftime('%H%M%S')}_{file_input.name}"
                            with open(os.path.join("yuklenen_belgeler", f_adi), "wb") as f: f.write(file_input.getbuffer())
                        
                        yeni_msg = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": u_mail, "Sifre": str(u_sifre), "Mudurluk": u_mud, "Mesaj": msg_input, "Dosya_Adi": f_adi, "Kimden": "Vatandaş"}
                        pd.DataFrame([yeni_msg]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.rerun()

# --- 🏢 MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_birim = st.selectbox("Müdürlüğünüz:", tum_birimler, key="adm_b")
    adm_sifre = st.text_input("Şifre:", type="password", key="adm_s")
    if adm_sifre == "1234":
        st.markdown(f"#### {adm_birim} - Gelen Sohbetler")
        df_all = mesaj_yukle()
        birim_msj = df_all[df_all["Mudurluk"] == adm_birim]
        
        # Bu müdürlüğe yazan benzersiz vatandaşlar
        vatandaslar = birim_msj["Gonderen"].unique()
        
        if len(vatandaslar) > 0:
            secilen_v = st.selectbox("Sohbet Edilecek Vatandaş:", vatandaslar)
            v_sohbet = birim_msj[birim_msj["Gonderen"] == secilen_v]
            
            # Sohbeti Göster
            for _, sm in v_sohbet.iterrows():
                with st.chat_message("user" if sm["Kimden"] == "Vatandaş" else "assistant"):
                    st.write(f"**{sm['Kimden']} ({sm['Tarih']}):** {sm['Mesaj']}")
                    if sm["Dosya_Adi"] != "Yok":
                        yol = "yuklenen_belgeler" if sm["Kimden"] == "Vatandaş" else "belediye_belgeleri"
                        if os.path.exists(os.path.join(yol, str(sm["Dosya_Adi"]))):
                            with open(os.path.join(yol, str(sm["Dosya_Adi"])), "rb") as f:
                                st.markdown(dosya_indirme_linki(f.read(), str(sm["Dosya_Adi"])), unsafe_allow_html=True)
            
            # Cevap Yaz
            with st.form("admin_reply"):
                a_msg = st.text_area("Cevabınız:")
                a_file = st.file_uploader("Dosya Gönder:")
                if st.form_submit_button("Yanıtı Gönder"):
                    if a_msg:
                        af_adi = "Yok"
                        if a_file:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            af_adi = f"belediye_{datetime.now().strftime('%H%M')}_{a_file.name}"
                            with open(os.path.join("belediye_belgeleri", af_adi), "wb") as f: f.write(a_file.getbuffer())
                        
                        yeni_reply = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": secilen_v, "Sifre": v_sohbet.iloc[0]["Sifre"], "Mudurluk": adm_birim, "Mesaj": a_msg, "Dosya_Adi": af_adi, "Kimden": "Müdürlük"}
                        pd.DataFrame([yeni_reply]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                        st.success("Mesaj vatandaşa iletildi."); st.rerun()
        else: st.info("Bu birime henüz bir mesaj gelmemiş.")
