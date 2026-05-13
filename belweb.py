import streamlit as st
import pandas as pd
import os
import re
import base64
import time
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- REGEX VE FONKSİYONLAR ---
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
PHONE_PATTERN = r'^05[0-9]{9}$'

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
    if not os.path.exists(dosya_yolu): return f"⚠️ {dosya_adi} yok"
    with open(dosya_yolu, "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold;">📩 {etiket}</a>'

# MÜDÜRLÜKLER VE TÜRLER
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak İşlemleri", "Nikah Başvurusu", "Asker Ailesi Yardımı", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol Onarım", "Kaldırım Hasarı", "Asfalt Talebi", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü Kirliliği", "Kaldırım İşgali", "Denetim", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat İşlemleri", "Kaçak Yapı İhbarı", "Numarataj", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak Hayvanı Tedavi", "İlaçlama", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Emlak Vergisi", "Borç Yapılandırma", "Ödeme", "Diğer"],
    "Emlak ve İstimlak Müdürlüğü": ["Taşınmaz Kiralama", "Yer Tahsisi", "Diğer"],
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": ["Geri Dönüşüm", "Atık Toplama", "Diğer"],
    "Destek Hizmetleri Müdürlüğü": ["İhale Bilgisi", "Tedarikçi Kaydı", "Diğer"],
    "Yapı Kontrol Müdürlüğü": ["Riskli Bina", "İskan Kontrolü", "Diğer"]
}
tum_birimler = sorted(list(sikayet_turleri_dict.keys()))

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
        st.info("### 👤 Vatandaş Portalı\nAkıllı Asistan ile hızlıca talep oluşturun ve takip edin.")
        if st.button("Vatandaş Girişi", use_container_width=True):
            st.session_state.portal_modu = "vatandas"; st.rerun()
    with cm:
        st.success("### 🏢 Müdürlük Paneli\nYetkili girişi yaparak talepleri yönetin.")
        if st.button("Müdürlük Girişi", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"; st.rerun()

# --- 👤 2. EKRAN: VATANDAŞ PORTALI ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Ekrana Dön"): 
        st.session_state.portal_modu = "karşılama"; st.session_state.sayfa = "asistan_ana"; st.rerun()

    if st.session_state.sayfa == "asistan_ana":
        st.markdown("### 🤖 Akıllı Asistan: Size Nasıl Yardımcı Olabilirim?")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📝 Yeni Talep", use_container_width=True): st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Takip & Sohbet", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("📄 Evrak Rehberi", use_container_width=True): st.session_state.sayfa = "evrak_rehberi"; st.rerun()
        if c4.button("💬 Müdürlükle Konuş", use_container_width=True): st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.container(border=True):
            c1, c2 = st.columns(2)
            ad = c1.text_input("Ad"); soyad = c2.text_input("Soyad")
            ep = c1.text_input("E-posta"); tel = c2.text_input("Telefon (05xx...)")
            mud_sec = st.selectbox("Müdürlük", tum_birimler)
            tur_sec = st.selectbox("Talep Türü", sikayet_turleri_dict.get(mud_sec, ["Genel"]))
            det = st.text_area("Detaylar")
            if st.button("Talebi Gönder"):
                if ad and soyad and re.match(EMAIL_PATTERN, ep, re.IGNORECASE) and re.match(PHONE_PATTERN, tel):
                    sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                    pd.DataFrame([{"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel, "Müdürlük": mud_sec, "Tür": tur_sec, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success("✅ Talebiniz başarıyla iletildi! Takip ID: " + sid)
                    time.sleep(2); st.rerun()
                else: st.error("Lütfen tüm alanları doğru formatta doldurun.")

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Takip ve Sorgulama")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.container(border=True):
            c1, c2 = st.columns(2)
            arama = c1.text_input("E-posta veya Telefon")
            sf = c2.text_input("Sohbet Şifreniz", type="password")
            if arama:
                temiz = tel_temizle(arama)
                df_t = veri_yukle()
                if not df_t.empty:
                    res_t = df_t[(df_t["E-posta"] == arama) | (df_t["Telefon"].apply(tel_temizle) == temiz)]
                    if not res_t.empty: st.markdown("#### 📋 Talepleriniz"), st.table(res_t[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
                df_m = mesaj_yukle()
                if not df_m.empty:
                    k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == temiz)) & (df_m["Sifre"].astype(str) == str(sf))]
                    if not k_msg.empty:
                        st.divider(); st.markdown("#### 💬 Sohbet Geçmişi")
                        b_sec = st.radio("Birim:", k_msg["Mudurluk"].unique(), horizontal=True)
                        current = k_msg[k_msg["Mudurluk"] == b_sec]
                        for _, r in current.iterrows():
                            with st.chat_message("user"):
                                st.write(f"**{r['Ad']} {r['Soyad']}:** {r['Mesaj']}")
                                if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                            if r['Cevap'] != "Bekleniyor":
                                with st.chat_message("assistant"): st.write(f"**Belediye:** {r['Cevap']}")
                        with st.expander("📥 Yanıt Yaz / Belge Gönder"):
                            with st.form("q_rep"):
                                rm = st.text_area("Mesaj"); rf = st.file_uploader("Belge")
                                if st.form_submit_button("Yanıtı Gönder"):
                                    fn = "Yok"
                                    if rf:
                                        if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                        fn = f"rep_{datetime.now().strftime('%H%M%S')}_{rf.name}"
                                        with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(rf.getbuffer())
                                    pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": current.iloc[0]["Ad"], "Soyad": current.iloc[0]["Soyad"], "Gonderen": arama, "Telefon": temiz, "Sifre": sf, "Mudurluk": b_sec, "Mesaj": rm, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                                    st.success("✅ Yanıtınız iletildi!")
                                    time.sleep(2); st.rerun()

    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Yeni Sohbet")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.container(border=True):
            with st.form("init_chat"):
                c1, c2 = st.columns(2)
                u_ad = c1.text_input("Ad"); u_soyad = c2.text_input("Soyad")
                u_mail = c1.text_input("E-posta"); u_tel = c2.text_input("Telefon (05xx...)")
                u_pass = st.text_input("Sohbet Şifresi Belirle", type="password")
                u_mud = st.selectbox("Birim", tum_birimler)
                u_msg = st.text_area("Mesaj"); u_f = st.file_uploader("Belge")
                if st.form_submit_button("Sohbeti Başlat"):
                    if u_ad and u_soyad and re.match(EMAIL_PATTERN, u_mail) and re.match(PHONE_PATTERN, u_tel):
                        fn = "Yok"
                        if u_f:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            fn = f"init_{datetime.now().strftime('%H%M%S')}_{u_f.name}"
                            with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(u_f.getbuffer())
                        pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": u_ad, "Soyad": u_soyad, "Gonderen": u_mail, "Telefon": u_tel, "Sifre": u_pass, "Mudurluk": u_mud, "Mesaj": u_msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.success("✅ Mesajınız başarıyla iletildi!")
                        time.sleep(2); st.rerun()

    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Evrak Rehberi")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        m_s = st.selectbox("Müdürlük Seç", tum_birimler)
        for e in sikayet_turleri_dict.get(m_s, ["Genel"]): st.write(f"✅ {e}")

# --- 🏢 3. EKRAN: MÜDÜRLÜK PANELİ ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Karşılama"): st.session_state.portal_modu = "karşılama"; st.rerun()
    st.markdown("### 🏢 Müdürlük Paneli")
    c1, c2 = st.columns(2)
    adm_b = c1.selectbox("Biriminiz:", tum_birimler); adm_s = c2.text_input("Şifre:", type="password")
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Talepler", "💬 Sohbetler"])
        with t1:
            df_t = veri_yukle()
            if not df_t.empty:
                filt = df_t[df_t["Müdürlük"] == adm_b]
                st.dataframe(filt, use_container_width=True)
                if not filt.empty:
                    sid = st.selectbox("ID Seç:", filt["ID"].tolist())
                    with st.container(border=True):
                        cd, cs = st.columns(2)
                        yd = cd.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                        ys = cs.selectbox("Sevk:", tum_birimler, index=tum_birimler.index(adm_b))
                        ans = st.text_area("Yanıt:")
                        if st.button("Güncelle"):
                            idx = df_t[df_t["ID"] == sid].index
                            df_t.at[idx[0], "Belediye_Cevabi"] = ans
                            df_t.at[idx[0], "Durum"] = yd if ys == adm_b else "Sevk Edildi"
                            df_t.at[idx[0], "Müdürlük"] = ys
                            df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                            st.success("✅ Güncellendi!")
                            time.sleep(1.5); st.rerun()
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Vatandaş Ara (Mail/Tel):")
            v_l = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                vs = st.selectbox("Seç:", v_l); vg = bm[bm["Gonderen"] == vs]
                for _, r in vg.iterrows():
                    with st.container(border=True):
                        st.info(f"👤 {r['Ad']} {r['Soyad']}: {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Dosyayı Gör"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Cevabınız: {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Cevap"); f = st.file_uploader("Belge")
                    if st.form_submit_button("Yanıtla"):
                        fn = "Yok"
                        if f:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            fn = f"adm_{datetime.now().strftime('%H%M%S')}_{f.name}"
                            with open(os.path.join("belediye_belgeleri", fn), "wb") as file: file.write(f.getbuffer())
                        df_m.at[vg.index[-1], "Cevap"] = a; df_m.at[vg.index[-1], "Mudurluk_Dosya"] = fn
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                        st.success("✅ Yanıtınız iletildi!")
                        time.sleep(1.5); st.rerun()
