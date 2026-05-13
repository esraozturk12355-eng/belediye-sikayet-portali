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
        try: return pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
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

# --- VERİ VE SABİTLER ---
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + [
    "Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", 
    "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"
])))

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
    st.write("---")
    cv, cm = st.columns(2)
    with cv:
        st.info("### 👤 Vatandaş Portalı\nTalep oluşturma ve hızlı işlemler için giriş yapın.")
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
        if c1.button("📝 Yeni Talep Oluştur", use_container_width=True): st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Talep Sorgula", use_container_width=True): st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("💬 Müdürlükle Konuş", use_container_width=True): st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()
        if c4.button("📄 Evrak Rehberi", use_container_width=True): st.session_state.sayfa = "evrak_rehberi"; st.rerun()

    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("y_talep"):
            c1, c2 = st.columns(2)
            ad = c1.text_input("Ad")
            ep = c1.text_input("E-posta")
            soyad = c2.text_input("Soyad")
            tel = c2.text_input("Tel")
            mud = st.selectbox("Müdürlük", tum_birimler)
            det = st.text_area("Detay")
            if st.form_submit_button("Kaydet"):
                sid = str(datetime.now().timestamp())[-6:]
                pd.DataFrame([{"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel_temizle(tel), "Müdürlük": mud, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Alındı! ID: {sid}")

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Taleplerim")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Tel")
        if arama:
            df = veri_yukle()
            if not df.empty:
                res = df[(df["E-posta"] == arama) | (df["Telefon"].apply(tel_temizle) == tel_temizle(arama))]
                st.table(res)

    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Sohbet")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        m_sorgu = st.text_input("E-posta/Tel:")
        m_sf = st.text_input("Şifre:", type="password")
        if m_sorgu and m_sf:
            df_m = mesaj_yukle()
            k_msg = df_m[((df_m["Gonderen"] == m_sorgu) | (df_m["Telefon"].apply(tel_temizle) == tel_temizle(m_sorgu))) & (df_m["Sifre"].astype(str) == str(m_sf))]
            if not k_msg.empty:
                b_sec = st.radio("Birim:", k_msg["Mudurluk"].unique(), horizontal=True)
                for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                    with st.chat_message("user"):
                        st.write(r['Mesaj'])
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                    if r['Cevap'] != "Bekleniyor":
                        with st.chat_message("assistant"):
                            st.write(r['Cevap'])
                            if r['Mudurluk_Dosya'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("belediye_belgeleri", str(r['Mudurluk_Dosya'])), str(r['Mudurluk_Dosya'])), unsafe_allow_html=True)
                with st.expander("Yanıtla"):
                    with st.form("rep"):
                        msg = st.text_area("Mesaj"); f = st.file_uploader("Belge")
                        if st.form_submit_button("Gönder"):
                            fn = "Yok"
                            if f:
                                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                fn = f"rep_{datetime.now().strftime('%H%M')}_{f.name}"
                                with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(f.getbuffer())
                            pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_msg.iloc[0]["Gonderen"], "Telefon": k_msg.iloc[0]["Telefon"], "Sifre": m_sf, "Mudurluk": b_sec, "Mesaj": msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                            st.rerun()
            else:
                st.info("💡 Henüz bir sohbetiniz yok. Yeni bir mesaj gönderin:")
                with st.form("new_chat"):
                    c_mud = st.selectbox("Birim", tum_birimler); c_mail = st.text_input("E-posta"); c_tel = st.text_input("Tel"); c_pass = st.text_input("Şifre")
                    c_txt = st.text_area("Mesaj")
                    c_f = st.file_uploader("Belge Ekle (Opsiyonel)") # BURASI GÜNCELLENDİ
                    if st.form_submit_button("Sohbeti Başlat"):
                        fn = "Yok"
                        if c_f:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            fn = f"init_{datetime.now().strftime('%H%M')}_{c_f.name}"
                            with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(c_f.getbuffer())
                        pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": c_mail, "Telefon": tel_temizle(c_tel), "Sifre": c_pass, "Mudurluk": c_mud, "Mesaj": c_txt, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.success("Başlatıldı!"); st.rerun()

    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Evrak Rehberi")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        st.selectbox("Müdürlük Seçin", tum_birimler)

# --- 🏢 3. EKRAN: MÜDÜRLÜK PORTALI ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Ekrana Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    st.markdown("### 🏢 Müdürlük Paneli")
    c1, c2 = st.columns(2)
    adm_b = c1.selectbox("Birim:", tum_birimler); adm_s = c2.text_input("Şifre:", type="password")
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Talepler", "💬 Sohbetler"])
        with t1:
            df_t = veri_yukle()
            if not df_t.empty:
                filt = df_t[df_t["Müdürlük"] == adm_b]
                st.dataframe(filt)
                if not filt.empty:
                    sid = st.selectbox("ID Seç:", filt["ID"].tolist())
                    yd = st.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                    ys = st.selectbox("Sevk:", tum_birimler, index=tum_birimler.index(adm_b))
                    ans = st.text_area("Yanıt:")
                    if st.button("Kaydet"):
                        idx = df_t[df_t["ID"] == sid].index
                        df_t.at[idx[0], "Durum"] = yd if ys == adm_b else "Sevk Edildi"
                        df_t.at[idx[0], "Müdürlük"] = ys; df_t.at[idx[0], "Belediye_Cevabi"] = ans
                        df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig"); st.rerun()
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Vatandaş (E-posta/Tel):")
            v_l = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                vs = st.selectbox("Seç:", v_l); vg = bm[bm["Gonderen"] == vs]
                for _, r in vg.iterrows():
                    with st.container(border=True):
                        st.write(f"👤 {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Vatandaş Dosyası"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Cevap"); f = st.file_uploader("Belge")
                    if st.form_submit_button("Yanıtı Gönder"):
                        fn = "Yok"
                        if f:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            fn = f"adm_{datetime.now().strftime('%H%M')}_{f.name}"
                            with open(os.path.join("belediye_belgeleri", fn), "wb") as fi: fi.write(f.getbuffer())
                        df_m.at[vg.index[-1], "Cevap"] = a; df_m.at[vg.index[-1], "Mudurluk_Dosya"] = fn
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig"); st.rerun()
