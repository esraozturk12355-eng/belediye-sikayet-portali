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
    if not os.path.exists(dosya_yolu): return f"⚠️ {dosya_adi} bulunamadı"
    with open(dosya_yolu, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold;">📩 {etiket}</a>'

# --- VERİ VE SABİTLER ---
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive|edu|gov|net)\.(com|com\.tr|net|org)$'
PHONE_PATTERN = r'^(0?)[5][0-9]{9}$'
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
    st.markdown("<h2 style='text-align: center;'>Lütfen Giriş Türünü Seçiniz</h2>", unsafe_allow_html=True)
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
        if c2.button("🔍 Talep Sorgula", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("💬 Müdürlükle Konuş", use_container_width=True): st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()
        if c4.button("📄 Evrak Rehberi", use_container_width=True): st.session_state.sayfa = "evrak_rehberi"; st.rerun()

    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Sohbet Girişi")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        
        # --- DİREKT AÇILAN KİMLİK BİLGİLERİ ---
        with st.form("sohbet_giris"):
            st.markdown("#### 👤 Bilgileriniz")
            col1, col2 = st.columns(2)
            u_ad = col1.text_input("Adınız")
            u_soyad = col2.text_input("Soyadınız")
            u_mail = col1.text_input("E-posta Adresiniz")
            u_tel = col2.text_input("Telefon Numaranız (05xx...)")
            u_pass = st.text_input("Sohbet Şifreniz (Eski mesajları görmek veya devam etmek için gereklidir)", type="password")
            u_mud = st.selectbox("İletişime Geçilecek Birim", tum_birimler)
            
            st.markdown("---")
            u_msg = st.text_area("Mesajınız (Yeni bir konu başlatacaksanız yazın)")
            u_file = st.file_uploader("Belge Ekle (Opsiyonel)")
            
            submit = st.form_submit_button("Bilgileri Doğrula ve Gönder/Sohbeti Aç")
            
            if submit:
                is_m_ok = bool(re.match(EMAIL_PATTERN, u_mail, re.IGNORECASE))
                is_p_ok = bool(re.match(PHONE_PATTERN, u_tel))
                
                if u_ad and u_soyad and is_m_ok and is_p_ok and u_pass:
                    # Kayıt işlemi (Sadece mesaj varsa)
                    fn = "Yok"
                    if u_msg or u_file:
                        if u_file:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            fn = f"init_{datetime.now().strftime('%H%M%S')}_{u_file.name}"
                            with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(u_file.getbuffer())
                        
                        pd.DataFrame([{
                            "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Ad": u_ad, "Soyad": u_soyad, "Gonderen": u_mail,
                            "Telefon": tel_temizle(u_tel), "Sifre": u_pass,
                            "Mudurluk": u_mud, "Mesaj": u_msg, "Dosya_Adi": fn,
                            "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"
                        }]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.success("Mesajınız iletildi! Sohbet geçmişinizi görmek için 'Talep Sorgula' ekranını kullanabilirsiniz.")
                    else:
                        st.info("💡 Sadece geçmişi görmek istiyorsanız 'Talep Sorgula' ekranına gidin. Bu ekran yeni iletişim içindir.")
                else:
                    st.error("Lütfen tüm alanları doğru formatta doldurduğunuzdan emin olun.")

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("y_tal"):
            c1, c2 = st.columns(2)
            ad = c1.text_input("Ad"); soyad = c2.text_input("Soyad")
            ep = c1.text_input("E-posta"); tel = c2.text_input("Tel")
            mud = st.selectbox("Birim", tum_birimler); det = st.text_area("Detay")
            if st.form_submit_button("Kaydet"):
                if re.match(EMAIL_PATTERN, ep, re.IGNORECASE) and re.match(PHONE_PATTERN, tel):
                    sid = str(datetime.now().timestamp())[-6:]
                    pd.DataFrame([{"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel_temizle(tel), "Müdürlük": mud, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success(f"Alındı! ID: {sid}"); st.balloons()

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Talep & Sohbet Takip")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Tel")
        sf = st.text_input("Şifre", type="password")
        if arama:
            temiz = tel_temizle(arama)
            # TALEPLER
            df_t = veri_yukle()
            if not df_t.empty:
                res_t = df_t[(df_t["E-posta"] == arama) | (df_t["Telefon"].apply(str).apply(tel_temizle) == temiz)]
                if not res_t.empty: st.table(res_t[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            # SOHBET
            df_m = mesaj_yukle()
            k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(str).apply(tel_temizle) == temiz)) & (df_m["Sifre"].astype(str) == str(sf))]
            if not k_msg.empty:
                st.divider()
                b_sec = st.radio("Sohbet Geçmişi:", k_msg["Mudurluk"].unique(), horizontal=True)
                for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                    with st.chat_message("user"):
                        st.write(r['Mesaj'])
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                    if r['Cevap'] != "Bekleniyor":
                        with st.chat_message("assistant"):
                            st.write(r['Cevap'])
                # Sorgu içinden yanıt verme
                with st.expander("Yanıt Yaz"):
                    with st.form("quick_rep"):
                        m = st.text_area("Mesaj"); f = st.file_uploader("Belge")
                        if st.form_submit_button("Yanıtı Gönder"):
                            fn = "Yok"
                            if f:
                                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                fn = f"rep_{datetime.now().strftime('%H%M%S')}_{f.name}"
                                with open(os.path.join("yuklenen_belgeler", fn), "wb") as file: file.write(f.getbuffer())
                            pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": k_msg.iloc[0]["Ad"], "Soyad": k_msg.iloc[0]["Soyad"], "Gonderen": k_msg.iloc[0]["Gonderen"], "Telefon": k_msg.iloc[0]["Telefon"], "Sifre": sf, "Mudurluk": b_sec, "Mesaj": m, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                            st.rerun()

    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Evrak Rehberi")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        st.selectbox("Müdürlük", tum_birimler)

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
            ara = st.text_input("Vatandaş Ara (E-posta/Tel):")
            v_l = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                vs = st.selectbox("Seç:", v_l); vg = bm[bm["Gonderen"] == vs]
                for _, r in vg.iterrows():
                    with st.container(border=True):
                        st.info(f"👤 **Vatandaş:** {r.get('Ad', '')} {r.get('Soyad', '')} ({r['Tarih']})\n\n**Mesaj:** {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok":
                            st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Dosyayı Gör"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Cevabınız: {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Cevap"); f = st.file_uploader("Belge Gönder")
                    if st.form_submit_button("Yanıtı Gönder"):
                        fn = "Yok"
                        if f:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            fn = f"adm_{datetime.now().strftime('%H%M%S')}_{f.name}"
                            with open(os.path.join("belediye_belgeleri", fn), "wb") as file: file.write(f.getbuffer())
                        df_m.at[vg.index[-1], "Cevap"] = a; df_m.at[vg.index[-1], "Mudurluk_Dosya"] = fn
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig"); st.rerun()
