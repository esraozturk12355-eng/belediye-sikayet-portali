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
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
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
c2.subheader("Vatandaş İletişim & Belge Paylaşım Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📝 Talep ve Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("🏢 Müdürlükle İletişime Geç"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()
    if col4.button("📞 İletişim"): st.info("📞 0 (362) 511 44 88")

# --- 📝 2. SAYFA: TALEP FORMU (İstediğin Orijinal Format) ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Yeni Şikayet / Talep Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="ad_yeni")
            eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = bool(re.match(email_pattern, eposta, re.IGNORECASE)) if eposta else False
            if eposta and not is_email_valid: st.warning("⚠️ Geçersiz e-posta!")
        with c2: 
            soyad = st.text_input("Soyadınız", key="soyad_yeni")
            telefon_input = st.text_input("Telefon Numaranız", key="tel_yeni")
        
        sec_mud = st.selectbox("İlgili Müdürlük", tum_birimler, key="mud_yeni")
        detay = st.text_area("Açıklama", key="detay_yeni")
        
        if st.button("Kaydet ve Gönder"):
            if ad and soyad and eposta and is_email_valid:
                sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni = {"ID": sid, "Sıra_No": 1, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(telefon_input), "Müdürlük": sec_mud, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Talebiniz Alındı! ID: {sid}"); st.balloons()
            else: st.error("Lütfen zorunlu alanları doldurun.")

# --- 🔍 3. SAYFA: SORGULAMA VE ÖZEL SOHBET ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sorgu = st.text_input("E-posta Adresiniz:")
    s_sorgu = st.text_input("Sohbet Şifreniz (Varsa):", type="password")
    
    if m_sorgu:
        df_s = veri_yukle()
        if not df_s.empty:
            res = df_s[df_s["E-posta"] == m_sorgu]
            if not res.empty: st.markdown("#### 📋 Şikayet Durumlarınız"), st.table(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])

        df_m = mesaj_yukle()
        kendi_msgs = df_m[(df_m["Gonderen"] == m_sorgu) & (df_m["Sifre"].astype(str) == str(s_sorgu))]
        if not kendi_msgs.empty:
            birim_list = kendi_msgs["Mudurluk"].unique().tolist()
            sec_b = st.radio("Hangi birimle olan görüşmeyi açmak istersiniz?", birim_list, horizontal=True)
            
            st.write("---")
            st.markdown(f"#### 💬 {sec_b} ile Sohbet")
            for idx, r in kendi_msgs[kendi_msgs["Mudurluk"] == sec_b].iterrows():
                with st.chat_message("user"):
                    st.write(f"**Siz:** {r['Mesaj']}")
                    if r['Dosya_Adi'] != "Yok": 
                        yol = os.path.join("yuklenen_belgeler", str(r['Dosya_Adi']))
                        if os.path.exists(yol):
                            with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(r['Dosya_Adi']), "Dosyanız"), unsafe_allow_html=True)
                if r['Cevap'] != "Bekleniyor":
                    with st.chat_message("assistant"):
                        st.write(f"**Belediye:** {r['Cevap']}")
                        if r['Mudurluk_Dosya'] != "Yok":
                            yol_b = os.path.join("belediye_belgeleri", str(r['Mudurluk_Dosya']))
                            if os.path.exists(yol_b):
                                with open(yol_b, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(r['Mudurluk_Dosya']), "Birim Belgesi"), unsafe_allow_html=True)

# --- 🏢 4. SAYFA: İLETİŞİM KANALI (Belge Gönderimli) ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlüğe Belge / Mesaj Gönder")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("msg_ilk", clear_on_submit=True):
        k_mud = st.selectbox("Hangi Birim?", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Sorgulama Şifresi Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Belge/Görsel Ekle:")
        if st.form_submit_button("Gönder"):
            if k_mail and k_sifre:
                d_adi = "Yok"
                if k_file:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    d_adi = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                    with open(os.path.join("yuklenen_belgeler", d_adi), "wb") as f: f.write(k_file.getbuffer())
                yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": d_adi, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
                pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("İletildi! Sorgulama & Sohbet kısmından takip edebilirsiniz.")

# --- 🏢 MÜDÜRLÜK PANELİ ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_b = st.selectbox("Biriminiz:", tum_birimler, key="adm_birim")
    adm_s = st.text_input("Şifre:", type="password", key="adm_pass")
    if adm_s == "1234":
        t1, t2 = st.tabs(["Şikayet Kayıtları", "💬 Sohbetler & Belgeler"])
        with t2:
            df_m = mesaj_yukle()
            birim_m = df_m[df_m["Mudurluk"] == adm_b]
            ara_v = st.text_input("🔍 Vatandaş E-posta ile Ara:")
            v_list = [v for v in birim_m["Gonderen"].unique() if ara_v.lower() in str(v).lower()]
            if v_list:
                v_sec = st.selectbox("Sohbet Edilecek Kullanıcı:", v_list)
                v_gecmis = birim_m[birim_m["Gonderen"] == v_sec]
                for idx, r in v_gecmis.iterrows():
                    with st.container(border=True):
                        st.write(f"📧 **{v_sec}** | 📅 {r['Tarih']}")
                        st.info(f"👤 Vatandaş: {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok":
                            yol = os.path.join("yuklenen_belgeler", str(r['Dosya_Adi']))
                            if os.path.exists(yol):
                                with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(r['Dosya_Adi']), "Vatandaş Belgesi"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": 
                            st.success(f"🏛️ Yanıtınız: {r['Cevap']}")
                            if r['Mudurluk_Dosya'] != "Yok": st.write(f"📎 Gönderdiğiniz: {r['Mudurluk_Dosya']}")
                
                y_not = st.text_area("Cevap Yazın:", key="ans_adm")
                y_file = st.file_uploader("Belge Gönder:", key="file_adm")
                if st.button("Yanıtı Gönder"):
                    m_d_adi = "Yok"
                    if y_file:
                        if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                        m_d_adi = f"belediye_{v_gecmis.index[-1]}_{y_file.name}"
                        with open(os.path.join("belediye_belgeleri", m_d_adi), "wb") as f: f.write(y_file.getbuffer())
                    df_m.at[v_gecmis.index[-1], "Cevap"] = y_not
                    df_m.at[v_gecmis.index[-1], "Mudurluk_Dosya"] = m_d_adi
                    df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                    st.success("Yanıt iletildi!"); st.rerun()
