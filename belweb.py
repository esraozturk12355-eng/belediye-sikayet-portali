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

# --- 📚 TAM KAPSAMLI EVRAK VERİTABANI ---
EVRAK_DATABANK = {
    "Destek Hizmetleri Müdürlüğü": {"İhale Dosyası": ["İmza Sirküleri", "Vezne Makbuzu"], "Tedarikçi Kaydı": ["Vergi Levhası", "Yetki Belgesi"]},
    "İmar ve Şehircilik Müdürlüğü": {"İnşaat Ruhsatı": ["Tapu Kaydı", "Proje"], "İskan": ["Enerji Kimliği", "SGK Belgesi"]},
    "Fen İşleri Müdürlüğü": {"Yol Onarımı": ["Konum", "Dilekçe"], "Kazı İzni": ["Proje Onayı", "Teminat"]}
    # ... Diğerleri rehber sayfasında dinamik listelenecektir.
}

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("talepler.csv"):
        try: return pd.read_csv("talepler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Telefon", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
    if os.path.exists("mesajlar.csv"):
        try: 
            df = pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
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

# MÜDÜRLÜKLER VE TÜRLER
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
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Dijital Vatandaş & Yönetim Portalı")
st.divider()

# --- 🚀 ANA KARŞILAMA EKRANI ---
if st.session_state.portal_modu == "karşılama":
    st.markdown("<h2 style='text-align: center;'>Lütfen Giriş Türünü Seçiniz</h2>", unsafe_allow_html=True)
    cv, cm = st.columns(2)
    with cv:
        if st.button("👤 Vatandaş Portalı", use_container_width=True):
            st.session_state.portal_modu = "vatandas"; st.rerun()
    with cm:
        if st.button("🏢 Müdürlük Paneli", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"; st.rerun()

# --- 👤 VATANDAŞ PORTALI ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Sayfaya Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["📝 Yeni Talep Oluştur", "🔍 Takip & Sohbet", "📄 Evrak Rehberi"])

    # --- TAB 1: YENİ TALEP ---
    with tab1:
        st.markdown("### 📝 Yeni Talep Formu")
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="ad_yeni")
            eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = bool(re.match(email_pattern, eposta, re.IGNORECASE)) if eposta else False
            if eposta and not is_email_valid: st.warning("⚠️ Geçerli bir e-posta giriniz!")
        with c2: 
            soyad = st.text_input("Soyadınız", key="soyad_yeni")
            telefon_input = st.text_input("Telefon Numaranız", key="tel_yeni")
        
        secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_yeni")
        tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Talep", "Bilgi Edinme", "Diğer"])
        sikayet_turu = st.selectbox("Talep Türü", tur_listesi, key="tur_yeni")
        detay = st.text_area("Talep Detayı", key="detay_yeni")
        
        if st.button("Talebi Kaydet"):
            if ad and soyad and eposta and is_email_valid and telefon_input:
                temiz_tel = tel_temizle(telefon_input)
                df_mevcut = veri_yukle()
                yeni_sira_no = 1
                if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns:
                    birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                    if not birim_kayitlari.empty: yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
                
                sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni_kayit = {
                    "ID": sid, "Sıra_No": yeni_sira_no, 
                    "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                    "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu,
                    "Detay": detay.replace(",", " "), "Durum": "İnceleniyor",
                    "Belediye_Cevabi": "Henüz cevaplanmadı"
                }
                pd.DataFrame([yeni_kayit]).to_csv("talepler.csv", mode='a', header=not os.path.exists("talepler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"✅ Başarıyla alınmıştır. Takip ID: {sid}"); st.balloons()
            else: st.error("Lütfen formu eksiksiz doldurunuz.")

    # --- TAB 2: TAKİP & SOHBET ---
    with tab2:
        st.markdown("### 🔍 Takip & Sohbet")
        arama = st.text_input("E-posta veya Telefon numaranızı giriniz", key="sorgu_input")
        sf = st.text_input("Sohbet Şifreniz", type="password")
        if arama:
            temiz_arama = tel_temizle(arama)
            df = veri_yukle()
            if not df.empty:
                df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
                sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
                if not sonuclar.empty:
                    st.info(f"Toplam {len(sonuclar)} adet kaydınız bulundu:")
                    st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            
            df_m = mesaj_yukle()
            if not df_m.empty:
                k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == temiz_arama)) & (df_m["Sifre"].astype(str) == str(sf))]
                if not k_msg.empty:
                    b_sec = st.radio("Sohbet:", k_msg["Mudurluk"].unique())
                    for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                        with st.chat_message("user"): st.write(r['Mesaj'])
                        if r['Cevap'] != "Bekleniyor":
                            with st.chat_message("assistant"): st.write(r['Cevap'])

    # --- TAB 3: EVRAK REHBERİ ---
    with tab3:
        st.markdown("### 📄 Evrak Rehberi")
        ms = st.selectbox("Müdürlük", list(EVRAK_DATABANK.keys()))
        is_ = st.selectbox("İşlem", list(EVRAK_DATABANK[ms].keys()))
        for b in EVRAK_DATABANK[ms][is_]: st.write(f"✅ {b}")

# --- 🏢 MÜDÜRLÜK PORTALI ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Sayfaya Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2: sifre = st.text_input("Şifre:", type="password", key="adm_pass")
    
    if sifre == "1234":
        t1, t2 = st.tabs(["📋 Talepler", "💬 Sohbetler"])
        with t1:
            df_t = veri_yukle()
            if not df_t.empty:
                filt = df_t[df_t["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
                if not filt.empty:
                    st.dataframe(filt)
                    sid = st.selectbox("İşlem ID:", filt["ID"].tolist())
                    c1, c2 = st.columns(2)
                    y_d = c1.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                    y_s = c2.selectbox("Sevk Et:", tum_birimler, index=tum_birimler.index(admin_birim))
                    ans = st.text_area("Yazılı Yanıtınız:")
                    if st.button("Kaydet ve Güncelle"):
                        idx = df_t[df_t["ID"] == sid].index
                        if df_t.at[idx[0], "Müdürlük"] != y_s:
                            h = df_t[df_t["Müdürlük"] == y_s]
                            df_t.at[idx[0], "Sıra_No"] = 1 if h.empty else h["Sıra_No"].max() + 1
                        df_t.at[idx[0], "Durum"] = y_d if y_s == admin_birim else "Sevk Edildi"
                        df_t.at[idx[0], "Müdürlük"] = y_s
                        df_t.at[idx[0], "Belediye_Cevabi"] = ans
                        df_t.to_csv("talepler.csv", index=False, encoding="utf-8-sig")
                        st.success("Güncellendi!"); st.rerun()
                else: st.info("Talep bulunmuyor.")
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == admin_birim]
            ara = st.text_input("Vatandaş Ara (E-posta/Tel):")
            vl = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if vl:
                vs = st.selectbox("Seç:", vl)
                vg = bm[bm["Gonderen"] == vs]
                for _, r in vg.iterrows():
                    st.info(f"👤 {r['Mesaj']}")
                    if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ {r['Cevap']}")
                with st.form("rep"):
                    a = st.text_area("Cevap:"); f = st.file_uploader("Dosya:")
                    if st.form_submit_button("Gönder"):
                        df_m.at[vg.index[-1], "Cevap"] = a
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                        st.rerun()
