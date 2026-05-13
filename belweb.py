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

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Telefon", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
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
    if tel.startswith("0"): return tel[1:]
    return tel

def dosya_indirme_linki(dosya_yolu, dosya_adi, etiket="İndir"):
    if not os.path.exists(dosya_yolu): return f"⚠️ {dosya_adi} bulunamadı"
    with open(dosya_yolu, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold;">📩 {etiket}</a>'

# --- VERİ VE SABİTLER ---
tum_birimler = sorted(["Destek Hizmetleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Fen İşleri Müdürlüğü", "Mali Hizmetler Müdürlüğü", "Veteriner İşleri Müdürlüğü", "Yapı Kontrol Müdürlüğü", "Yazı İşleri Müdürlüğü", "Zabıta Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "İmar ve Şehircilik Müdürlüğü"])

# --- SESSION STATE ---
if "portal_modu" not in st.session_state: st.session_state.portal_modu = "karşılama"
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan_ana"

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Dijital Vatandaş & Yönetim Portalı")
st.divider()

# --- 🚀 1. EKRAN: GİRİŞ SEÇİMİ ---
if st.session_state.portal_modu == "karşılama":
    st.markdown("<h2 style='text-align: center;'>Hoş Geldiniz! Lütfen Giriş Türünü Seçiniz</h2>", unsafe_allow_html=True)
    cv, cm = st.columns(2)
    with cv:
        if st.button("👤 Vatandaş Girişi", use_container_width=True):
            st.session_state.portal_modu = "vatandas"; st.rerun()
    with cm:
        if st.button("🏢 Müdürlük Girişi", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"; st.rerun()

# --- 👤 2. EKRAN: VATANDAŞ PORTALI ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Sayfaya Dön"): 
        st.session_state.portal_modu = "karşılama"; st.session_state.sayfa = "asistan_ana"; st.rerun()
    
    if st.session_state.sayfa == "asistan_ana":
        st.markdown("### 🤖 Akıllı Asistan")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📝 Yeni Talep", use_container_width=True): st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Sorgula & Sohbet", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("💬 Müdürlükle Konuş", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c4.button("📄 Evrak Rehberi", use_container_width=True): st.session_state.sayfa = "evrak_rehberi"; st.rerun()

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("y_tal"):
            ad = st.text_input("Ad"); ep = st.text_input("E-posta"); tel = st.text_input("Tel")
            mud = st.selectbox("Birim", tum_birimler); det = st.text_area("Detay")
            if st.form_submit_button("Kaydet"):
                sid = str(datetime.now().timestamp())[-6:]
                pd.DataFrame([{"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "E-posta": ep, "Telefon": tel_temizle(tel), "Müdürlük": mud, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Alındı! ID: {sid}")

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Takip & Sohbet")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Tel")
        sf = st.text_input("Şifre", type="password")
        if arama:
            temiz = tel_temizle(arama)
            df_m = mesaj_yukle()
            k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == temiz)) & (df_m["Sifre"].astype(str) == str(sf))]
            if not k_msg.empty:
                b_sec = st.radio("Sohbet:", k_msg["Mudurluk"].unique(), horizontal=True)
                for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                    with st.chat_message("user"):
                        st.write(r['Mesaj'])
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                    if r['Cevap'] != "Bekleniyor":
                        with st.chat_message("assistant"):
                            st.write(r['Cevap'])
                            if r['Mudurluk_Dosya'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("belediye_belgeleri", str(r['Mudurluk_Dosya'])), str(r['Mudurluk_Dosya'])), unsafe_allow_html=True)
                with st.expander("Yanıt Yaz"):
                    with st.form("rep"):
                        m = st.text_area("Mesaj"); f = st.file_uploader("Belge")
                        if st.form_submit_button("Gönder"):
                            fn = "Yok"
                            if f:
                                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                fn = f"rep_{datetime.now().strftime('%H%M')}_{f.name}"
                                with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(f.getbuffer())
                            pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_msg.iloc[0]["Gonderen"], "Telefon": k_msg.iloc[0]["Telefon"], "Sifre": sf, "Mudurluk": b_sec, "Mesaj": m, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                            st.rerun()

# --- 🏢 3. EKRAN: MÜDÜRLÜK PORTALI ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Ekrana Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    st.markdown("### 🏢 Müdürlük Paneli")
    c1, c2 = st.columns(2)
    adm_b = c1.selectbox("Birim:", tum_birimler); adm_s = c2.text_input("Şifre:", type="password")
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Talepler", "💬 Sohbetler"])
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Vatandaş (E-posta/Tel):")
            v_l = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                v_s = st.selectbox("Seç:", v_l); v_g = bm[bm["Gonderen"] == v_s]
                for _, r in v_g.iterrows():
                    with st.container(border=True):
                        st.info(f"👤 Vatandaş: {r['Mesaj']}")
                        # --- VATANDAŞIN BELGESİNİ BURADA GÖSTERİYORUZ ---
                        if r['Dosya_Adi'] != "Yok":
                            yol = os.path.join("yuklenen_belgeler", str(r['Dosya_Adi']))
                            st.markdown(dosya_indirme_linki(yol, str(r['Dosya_Adi']), "Vatandaşın Gönderdiği Belgeyi Görüntüle"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": 
                            st.success(f"🏛️ Cevabınız: {r['Cevap']}")
                            if r['Mudurluk_Dosya'] != "Yok":
                                st.write(f"📎 Gönderdiğiniz Ek: {r['Mudurluk_Dosya']}")
                
                with st.form("adm_rep"):
                    ans = st.text_area("Cevap"); f = st.file_uploader("Belge Gönder")
                    if st.form_submit_button("Yanıtı Gönder"):
                        fn = "Yok"
                        if f:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            fn = f"adm_{datetime.now().strftime('%H%M')}_{f.name}"
                            with open(os.path.join("belediye_belgeleri", fn), "wb") as fi: fi.write(f.getbuffer())
                        df_m.at[v_g.index[-1], "Cevap"] = ans; df_m.at[v_g.index[-1], "Mudurluk_Dosya"] = fn
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig"); st.rerun()
