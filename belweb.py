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

# --- VERİTABANI VE SABİTLER ---
EVRAK_DATABANK = {
    "Yazı İşleri Müdürlüğü": ["Nikah Başvurusu", "Asker Ailesi Yardımı", "Encümen Kararı Örneği"],
    "Fen İşleri Müdürlüğü": ["Yol Onarım", "Kaldırım Hasarı", "Kazı İzni"],
    "Zabıta Müdürlüğü": ["Pazar Yeri Tahsisi", "İşyeri Ruhsatı", "Gürültü Şikayeti"],
    "İmar ve Şehircilik Müdürlüğü": ["İnşaat Ruhsatı", "Yapı Kullanma İzni", "Numarataj"],
    "Veteriner İşleri Müdürlüğü": ["Sokak Hayvanı Tedavi", "Sahipli Hayvan Kaydı", "İlaçlama Talebi"],
    "Mali Hizmetler Müdürlüğü": ["Emlak Vergisi Bildirimi", "Rayiç Bedel Belgesi", "Borç Yapılandırma"],
    "Emlak ve İstimlak Müdürlüğü": ["Belediye Taşınmazı Kiralama", "Kamulaştırma Bilgi"],
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": ["Atık Yağ Toplama", "Geri Dönüşüm Kutusu"],
    "Destek Hizmetleri Müdürlüğü": ["İhale Dosyası Alımı", "Tedarikçi Kaydı"],
    "Yapı Kontrol Müdürlüğü": ["Kaçak Yapı İhbar", "Riskli Yapı Tespiti"]
}

sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(EVRAK_DATABANK.keys()))

EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
PHONE_PATTERN = r'^05[0-9]{9}$' # 0 ile başlayan 11 haneli numara

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
    if not os.path.exists(dosya_yolu): return "⚠️ Dosya bulunamadı"
    with open(dosya_yolu, "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold;">📩 {etiket}</a>'

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
        if st.button("👤 Vatandaş Girişi (Akıllı Asistan)", use_container_width=True):
            st.session_state.portal_modu = "vatandas"; st.rerun()
    with cm:
        if st.button("🏢 Müdürlük Yönetim Paneli", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"; st.rerun()

# --- 👤 2. EKRAN: VATANDAŞ PORTAL ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Karşılama Ekranına Dön"):
        st.session_state.portal_modu = "karşılama"; st.session_state.sayfa = "asistan_ana"; st.rerun()

    if st.session_state.sayfa == "asistan_ana":
        st.markdown("### 🤖 Akıllı Asistan: Size Nasıl Yardımcı Olabilirim?")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📝 Yeni Talep Oluştur", use_container_width=True): st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Talep & Sohbet Sorgula", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("📄 Evrak Rehberi", use_container_width=True): st.session_state.sayfa = "evrak_rehberi"; st.rerun()
        if c4.button("💬 Müdürlükle Konuş", use_container_width=True): st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("y_tal_form"):
            c1, c2 = st.columns(2)
            ad = c1.text_input("Adınız")
            soyad = c2.text_input("Soyadınız")
            ep = c1.text_input("E-posta Adresiniz")
            tel = c2.text_input("Telefon Numaranız (05xx...)")
            
            mud = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler)
            tur = st.selectbox("Talep Türünü Seçiniz", sikayet_turleri_dict.get(mud, ["Genel Talep", "Diğer"]))
            det = st.text_area("Talep Detayları")
            
            if st.form_submit_button("Talebi Gönder"):
                if ad and soyad and re.match(EMAIL_PATTERN, ep, re.IGNORECASE) and re.match(PHONE_PATTERN, tel):
                    sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                    yeni_t = {"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel, "Müdürlük": mud, "Tür": tur, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}
                    pd.DataFrame([yeni_t]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success(f"✅ Talebiniz Alındı! Takip ID: {sid}"); st.balloons()
                else: st.error("Lütfen tüm alanları doğru formatta doldurun (Telefon 05... ile 11 hane olmalı).")

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Talep Sorgulama & Sohbet Geçmişi")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
        sf_kod = st.text_input("Sohbet Şifreniz (Varsa):", type="password")
        if arama:
            temiz = tel_temizle(arama)
            df_t = veri_yukle()
            if not df_t.empty:
                res_t = df_t[(df_t["E-posta"] == arama) | (df_t["Telefon"].apply(tel_temizle) == temiz)]
                if not res_t.empty: st.markdown("#### 📋 Talepleriniz"), st.table(res_t[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            
            df_m = mesaj_yukle()
            if not df_m.empty:
                k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == temiz)) & (df_m["Sifre"].astype(str) == str(sf_kod))]
                if not k_msg.empty:
                    st.divider(); st.markdown("#### 💬 Müdürlükle Sohbet")
                    b_sec = st.radio("Birim Seç:", k_msg["Mudurluk"].unique(), horizontal=True)
                    current = k_msg[k_msg["Mudurluk"] == b_sec]
                    for _, r in current.iterrows():
                        with st.chat_message("user"):
                            st.write(r['Mesaj'])
                            if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor":
                            with st.chat_message("assistant"):
                                st.write(r['Cevap'])
                                if r['Mudurluk_Dosya'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("belediye_belgeleri", str(r['Mudurluk_Dosya'])), str(r['Mudurluk_Dosya'])), unsafe_allow_html=True)
                    
                    with st.expander("📥 Yanıt Yaz / Belge Gönder"):
                        with st.form("q_rep"):
                            rm = st.text_area("Mesaj"); rf = st.file_uploader("Belge")
                            if st.form_submit_button("Yanıtı Gönder"):
                                fn = "Yok"
                                if rf:
                                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                    fn = f"rep_{datetime.now().strftime('%H%M')}_{rf.name}"
                                    with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(rf.getbuffer())
                                pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": current.iloc[0]["Ad"], "Soyad": current.iloc[0]["Soyad"], "Gonderen": current.iloc[0]["Gonderen"], "Telefon": current.iloc[0]["Telefon"], "Sifre": sf_kod, "Mudurluk": b_sec, "Mesaj": rm, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                                st.success("Gönderildi!"); st.rerun()

    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Konuşma Başlat")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("sohbet_init"):
            c1, c2 = st.columns(2)
            u_ad = c1.text_input("Ad"); u_soyad = c2.text_input("Soyad")
            u_mail = c1.text_input("E-posta"); u_tel = c2.text_input("Telefon (05xx...)")
            u_pass = st.text_input("Şifre Belirle (Sorgulama için)", type="password")
            u_mud = st.selectbox("Birim", tum_birimler); u_msg = st.text_area("Mesaj"); u_f = st.file_uploader("Belge Yükle")
            if st.form_submit_button("Sohbeti Başlat"):
                if u_ad and u_soyad and re.match(EMAIL_PATTERN, u_mail) and re.match(PHONE_PATTERN, u_tel):
                    fn = "Yok"
                    if u_f:
                        if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                        fn = f"init_{datetime.now().strftime('%H%M')}_{u_f.name}"
                        with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(u_f.getbuffer())
                    pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": u_ad, "Soyad": u_soyad, "Gonderen": u_mail, "Telefon": u_tel, "Sifre": u_pass, "Mudurluk": u_mud, "Mesaj": u_msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                    st.success("Mesaj iletildi!"); st.rerun()

    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Evrak Rehberi")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        m_sec = st.selectbox("Müdürlük Seçiniz", tum_birimler)
        for e in EVRAK_DATABANK.get(m_sec, ["Genel Dilekçe"]): st.write(f"✅ {e}")

# --- 🏢 3. EKRAN: MÜDÜRLÜK PANELİ ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Karşılama Ekranına Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    c1, c2 = st.columns(2)
    adm_b = c1.selectbox("Müdürlüğünüz:", tum_birimler)
    adm_s = c2.text_input("Yetkili Şifresi:", type="password")
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Talepleri Yönet", "💬 Sohbetler"])
        with t1:
            df_t = veri_yukle()
            if not df_t.empty:
                filt = df_t[df_t["Müdürlük"] == adm_b]
                st.dataframe(filt, use_container_width=True)
                if not filt.empty:
                    sid = st.selectbox("İşlem Yapılacak ID:", filt["ID"].tolist())
                    with st.container(border=True):
                        c_d, c_s = st.columns(2)
                        y_durum = c_d.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                        y_sevk = c_s.selectbox("Sevk Et:", tum_birimler, index=tum_birimler.index(adm_b))
                        ans_t = st.text_area("Vatandaşa Yanıt:")
                        if st.button("Talebi Güncelle"):
                            idx = df_t[df_t["ID"] == sid].index
                            df_t.at[idx[0], "Belediye_Cevabi"] = ans_t
                            df_t.at[idx[0], "Durum"] = y_durum if y_sevk == adm_b else "Sevk Edildi"
                            df_t.at[idx[0], "Müdürlük"] = y_sevk
                            df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig"); st.success("Başarılı!"); st.rerun()
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Vatandaş Ara (Tel/Mail):")
            v_l = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                v_s = st.selectbox("Seç:", v_l); v_g = bm[bm["Gonderen"] == v_s]
                for _, r in v_g.iterrows():
                    with st.container(border=True):
                        st.info(f"👤 {r['Ad']} {r['Soyad']} ({r['Tarih']}): {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Vatandaşın Belgesi"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Cevabınız: {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Yanıtınız:"); f = st.file_uploader("Belge Gönder")
                    if st.form_submit_button("Yanıtı Gönder"):
                        fn = "Yok"
                        if f:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            fn = f"adm_{datetime.now().strftime('%H%M')}_{f.name}"
                            with open(os.path.join("belediye_belgeleri", fn), "wb") as file: file.write(f.getbuffer())
                        df_m.at[v_g.index[-1], "Cevap"] = a; df_m.at[v_g.index[-1], "Mudurluk_Dosya"] = fn
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig"); st.rerun()
