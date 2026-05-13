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

# --- REGEX DESENLERİ ---
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive|edu|gov|net)\.(com|com\.tr|net|org)$'
PHONE_PATTERN = r'^(0?)[5][0-9]{9}$'

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Ad", "Soyad", "Gonderen", "Telefon", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
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
    if not os.path.exists(dosya_yolu): return "⚠️ Dosya Yok"
    with open(dosya_yolu, "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

# MÜDÜRLÜK LİSTESİ
tum_birimler = sorted(["Destek Hizmetleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Fen İşleri Müdürlüğü", "Mali Hizmetler Müdürlüğü", "Veteriner İşleri Müdürlüğü", "Yapı Kontrol Müdürlüğü", "Yazı İşleri Müdürlüğü", "Zabıta Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "İmar ve Şehircilik Müdürlüğü"])

# --- SESSION STATE ---
if "portal_modu" not in st.session_state: st.session_state.portal_modu = "karşılama"
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan_ana"
if "auth_ok" not in st.session_state: st.session_state.auth_ok = False

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
        st.session_state.portal_modu = "karşılama"
        st.session_state.sayfa = "asistan_ana"
        st.session_state.auth_ok = False
        st.rerun()
    
    if st.session_state.sayfa == "asistan_ana":
        st.markdown("### 🤖 Akıllı Asistan: Size Nasıl Yardımcı Olabilirim?")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📝 Yeni Talep Oluştur", use_container_width=True): st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Talep & Sohbet Sorgula", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("💬 Müdürlükle Konuş", use_container_width=True): st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()
        if c4.button("📄 Evrak Rehberi", use_container_width=True): st.session_state.sayfa = "evrak_rehberi"; st.rerun()

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("y_tal"):
            c1, c2 = st.columns(2)
            ad = c1.text_input("Ad"); soyad = c2.text_input("Soyad")
            ep = c1.text_input("E-posta"); tel = c2.text_input("Tel (05xx...)")
            mud = st.selectbox("Birim", tum_birimler); det = st.text_area("Talep Detayı")
            if st.form_submit_button("Talebi Kaydet"):
                if re.match(EMAIL_PATTERN, ep, re.IGNORECASE) and re.match(PHONE_PATTERN, tel):
                    sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                    yeni = {"ID": sid, "Sıra_No": 1, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel_temizle(tel), "Müdürlük": mud, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
                    pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success(f"Talebiniz Alındı! ID: {sid}"); st.balloons()
                else: st.error("Lütfen e-posta ve telefon formatını kontrol edin.")

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Talep Sorgulama & Sohbet Geçmişi")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
        sf_chat = st.text_input("Mesaj Şifreniz (Varsa):", type="password")
        if arama:
            temiz_arama = tel_temizle(arama)
            df_t = veri_yukle()
            if not df_t.empty:
                res_t = df_t[(df_t["E-posta"] == arama) | (df_t["Telefon"].apply(str).apply(tel_temizle) == temiz_arama)]
                if not res_t.empty:
                    st.markdown("#### 📋 Taleplerinizin Durumu")
                    st.table(res_t[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            
            df_m = mesaj_yukle()
            if not df_m.empty:
                k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(str).apply(tel_temizle) == temiz_arama)) & (df_m["Sifre"].astype(str) == str(sf_chat))]
                if not k_msg.empty:
                    st.markdown("#### 💬 Sohbet Geçmişi")
                    b_sec = st.radio("Birim Seç:", k_msg["Mudurluk"].unique(), horizontal=True)
                    for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                        with st.chat_message("user"): st.write(r['Mesaj'])
                        if r['Cevap'] != "Bekleniyor":
                            with st.chat_message("assistant"): st.write(r['Cevap'])

    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Sohbet")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.session_state.auth_ok = False; st.rerun()
        
        with st.container(border=True):
            st.markdown("#### 👤 Kimlik Bilgileriniz")
            c1, c2 = st.columns(2)
            u_ad = c1.text_input("Ad")
            u_soyad = c2.text_input("Soyad")
            c3, c4, c5 = st.columns(3)
            u_mail = c3.text_input("E-posta")
            u_tel = c4.text_input("Telefon (05xx...)")
            u_pass = c5.text_input("Sohbet Şifreniz", type="password")
            
            is_m_ok = bool(re.match(EMAIL_PATTERN, u_mail, re.IGNORECASE)) if u_mail else False
            is_p_ok = bool(re.match(PHONE_PATTERN, u_tel)) if u_tel else False
            
            if st.button("Onayla ve Başla"):
                if u_ad and u_soyad and is_m_ok and is_p_ok and u_pass:
                    st.session_state.auth_ok = True; st.session_state.u_ad = u_ad; st.session_state.u_soyad = u_soyad
                    st.session_state.u_mail = u_mail; st.session_state.u_tel = u_tel; st.session_state.u_pass = u_pass
                    st.rerun()
                else: st.error("Hatalı format veya eksik bilgi!")

        if st.session_state.auth_ok:
            df_m = mesaj_yukle()
            u_temiz_tel = tel_temizle(st.session_state.u_tel)
            k_msg = df_m[((df_m["Gonderen"] == st.session_state.u_mail) | (df_m["Telefon"].apply(str).apply(tel_temizle) == u_temiz_tel)) & (df_m["Sifre"].astype(str) == str(st.session_state.u_pass))]
            
            if not k_msg.empty:
                b_sec = st.radio("Birim:", k_msg["Mudurluk"].unique(), horizontal=True)
                for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                    with st.chat_message("user"):
                        st.write(r['Mesaj'])
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                    if r['Cevap'] != "Bekleniyor":
                        with st.chat_message("assistant"): st.write(r['Cevap'])
                with st.expander("Yanıt Yaz"):
                    with st.form("rep_form"):
                        m = st.text_area("Mesaj"); f = st.file_uploader("Belge")
                        if st.form_submit_button("Gönder"):
                            fn = "Yok"
                            if f:
                                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                fn = f"rep_{datetime.now().strftime('%H%M')}_{f.name}"
                                with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(f.getbuffer())
                            pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": st.session_state.u_ad, "Soyad": st.session_state.u_soyad, "Gonderen": st.session_state.u_mail, "Telefon": u_temiz_tel, "Sifre": st.session_state.u_pass, "Mudurluk": b_sec, "Mesaj": m, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                            st.rerun()
            else:
                with st.form("new_init"):
                    target_m = st.selectbox("Birim Seçiniz", tum_birimler)
                    m_txt = st.text_area("Mesaj"); m_f = st.file_uploader("Belge")
                    if st.form_submit_button("Sohbeti Başlat"):
                        fn = "Yok"
                        if m_f:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            fn = f"init_{datetime.now().strftime('%H%M')}_{m_f.name}"
                            with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(m_f.getbuffer())
                        pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": st.session_state.u_ad, "Soyad": st.session_state.u_soyad, "Gonderen": st.session_state.u_mail, "Telefon": u_temiz_tel, "Sifre": st.session_state.u_pass, "Mudurluk": target_m, "Mesaj": m_txt, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.success("İletildi!"); st.rerun()

    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Evrak Rehberi")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        st.selectbox("Müdürlük", tum_birimler)

# --- 🏢 3. EKRAN: MÜDÜRLÜK PORTALI ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Ekrana Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    st.markdown("### 🏢 Müdürlük Yönetim Paneli")
    c1, c2 = st.columns(2)
    adm_b = c1.selectbox("Biriminiz:", tum_birimler)
    adm_s = c2.text_input("Şifre:", type="password")
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Talepler", "💬 Sohbetler"])
        with t1:
            df_t = veri_yukle()
            if not df_t.empty:
                filt = df_t[df_t["Müdürlük"] == adm_b]
                if not filt.empty:
                    st.dataframe(filt, use_container_width=True)
                    st.write("---")
                    st.markdown("#### 📩 Talebi Yanıtla & Güncelle")
                    sid = st.selectbox("İşlem Yapılacak ID Seç:", filt["ID"].tolist())
                    with st.container(border=True):
                        cd, cs = st.columns(2)
                        y_durum = cd.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                        y_sevk = cs.selectbox("Sevk Et:", tum_birimler, index=tum_birimler.index(adm_b))
                        y_cevap = st.text_area("Vatandaşa Yazılı Cevap:")
                        if st.button("Talebi Onayla ve Gönder"):
                            idx = df_t[df_t["ID"] == sid].index
                            df_t.at[idx[0], "Belediye_Cevabi"] = y_cevap
                            df_t.at[idx[0], "Durum"] = y_durum if y_sevk == adm_b else "Sevk Edildi"
                            df_t.at[idx[0], "Müdürlük"] = y_sevk
                            df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                            st.success("Talep güncellendi!"); st.rerun()
                else: st.info("Bu birime ait talep bulunmuyor.")
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Vatandaş Ara (E-posta/Tel):")
            v_l = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                vs = st.selectbox("Seç:", v_l); vg = bm[bm["Gonderen"] == vs]
                for _, r in vg.iterrows():
                    with st.container(border=True):
                        st.info(f"👤 {r['Mesaj']}")
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Cevap"); f = st.file_uploader("Belge Gönder")
                    if st.form_submit_button("Yanıtı Gönder"):
                        df_m.at[vg.index[-1], "Cevap"] = a; df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig"); st.rerun()
