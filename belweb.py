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

# --- DETAYLI EVRAK VERİTABANI ---
EVRAK_DATABANK = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Kaydı", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi", "Zemin Etüd Raporu"],
        "Yapı Kullanma İzin Belgesi (İskan)": ["Enerji Kimlik Belgesi", "Sığınak Onay Yazısı", "SGK İlişiksiz Belgesi", "İtfaiye Uygunluk Raporu", "Asansör Tescil Belgesi"],
        "Numarataj İşlemleri": ["Tapu Fotokopisi", "Yapı Ruhsatı", "Kimlik Fotokopisi", "Dilekçe", "Eski Kapı Numarası (Varsa)"],
        "Yıkım Ruhsatı": ["Tapu Kaydı", "Yıkım Sorumlusu Belgesi", "İlgili Kurumların Kesme Yazıları", "Atık Yönetim Planı", "Fotoğraflar"],
        "İmar Durumu Talebi": ["Tapu Sureti", "Aplikasyon Krokisi", "Dilekçe", "Vekaletname (Gerekirse)", "Başvuru Ücreti Dekontu"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Kısıtlılık Belgesi (Emekli/Engelli)", "Dilekçe", "Rayiç Bedel Yazısı"],
        "Rayiç Bedel Belgesi": ["Tapu Bilgileri", "Borçsuzluk Belgesi", "Kimlik Fotokopisi", "Dilekçe", "İlgili Kişinin Vekaletnamesi"],
        "İlan ve Reklam Vergisi": ["Tabela Ölçüleri", "Vergi Levhası Fotokopisi", "Tabela Fotoğrafı", "Kira Kontratı", "Dilekçe"],
        "Çevre Temizlik Vergisi Kaydı": ["Tapu veya Kira Kontratı", "Vergi Levhası", "Su Faturası Örneği", "Kimlik Bilgileri", "Açılış Ruhsatı"],
        "Borç Yapılandırma": ["Kimlik Fotokopisi", "Başvuru Formu", "Mevcut Borç Dökümü", "Taahhütname", "İmza Sirküleri (Şirketler için)"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Raporu", "Oda Kayıt Belgesi", "Ustalık Belgesi"],
        "Pazar Yeri Tahsis": ["Oda Kayıt Belgesi", "İkametgah", "Sabıka Kaydı", "2 Adet Fotoğraf", "Sağlık Raporu"],
        "Hafta Tatili Ruhsatı": ["Mevcut İşyeri Ruhsatı", "Dilekçe", "Harç Dekontu", "Kimlik Fotokopisi", "Vergi Levhası"],
        "Canlı Müzik İzni": ["İşyeri Ruhsatı", "Çevresel Gürültü Raporu", "Akustik Rapor", "Başvuru Formu", "Dilekçe"],
        "İşgal Harcı Talebi": ["Tabela/Masa/Sandalye Ölçüleri", "Kira Kontratı", "Kroki", "Dilekçe", "Kimlik Fotokopisi"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe", "Fotoğraflı Kanıt", "Bina Sakinleri İmzası (Gerekirse)", "İletişim Bilgileri"],
        "Alt Yapı Kazı İzni": ["Proje Onayı", "AYKOME İzin Belgesi", "Teminat Dekontu", "İş Programı", "Güvenlik Tedbirleri Taahhütnamesi"],
        "Moloz Atım Talebi": ["Dilekçe", "Adres Bilgisi", "Harcın Ödendiğine Dair Makbuz", "Moloz Miktarı Beyanı", "Kimlik Fotokopisi"],
        "İş Makinesi Kiralama": ["Talep Dilekçesi", "Çalışma Yapılacak Alanın Tapusu", "Ödeme Dekontu", "Taahhütname", "Kimlik Bilgisi"],
        "Sokak Aydınlatma Talebi": ["Dilekçe", "Mahalle/Sokak Bilgisi", "Muhtar Onayı (Tavsiye)", "Aydınlatma İhtiyaç Nedeni", "Kroki"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası", "Sahibinin Kimlik Fotokopisi", "İkametgah"],
        "Sokak Hayvanı Tedavi Talebi": ["İhbar Dilekçesi", "Hayvanın Bulunduğu Konum", "Mümkünse Fotoğraf", "Bulunma Saati", "İrtibat Numarası"],
        "Pet Shop Denetim": ["İşyeri Ruhsatı", "Hayvan Satış Sertifikası", "Hijyen Belgesi", "Kapasite Beyanı", "Dilekçe"],
        "Isırma Vaka Takibi": ["Olay Yeri Raporu", "Sağlık Kuruluşu Sevk Belgesi", "Hayvan Bilgisi", "Şahit Varsa İsimleri", "Dilekçe"],
        "Vektörle Mücadele (İlaçlama)": ["Adres Bilgisi", "İlaçlama Nedeni", "Dilekçe", "Apartman Karar Defteri Sureti (Gerekirse)", "Kimlik Fotokopisi"]
    }
}

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

tum_birimler = list(EVRAK_DATABANK.keys()) + ["Destek Hizmetleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Yapı Kontrol Müdürlüğü", "Yazı İşleri Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü"]
tum_birimler = sorted(list(set(tum_birimler)))

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Vatandaş Portalı & Akıllı Rehber")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📝 Talep ve Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("📄 Gerekli Evraklar Rehberi"): st.session_state.sayfa = "evrak_ekrani"; st.rerun()
    if col4.button("🏢 Müdürlükle İletişime Geç"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()

# --- 📝 2. SAYFA: TALEP FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Yeni Şikayet / Talep Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="ad_yeni")
            eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
            is_valid = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', eposta)) if eposta else False
        with c2: 
            soyad = st.text_input("Soyadınız", key="soyad_yeni")
            tel = st.text_input("Telefon Numaranız", key="tel_yeni")
        sec_mud = st.selectbox("İlgili Müdürlük", tum_birimler, key="mud_yeni")
        detay = st.text_area("Açıklama", key="detay_yeni")
        if st.button("Kaydet ve Gönder"):
            if ad and soyad and is_valid:
                sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni = {"ID": sid, "Sıra_No": 1, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(tel), "Müdürlük": sec_mud, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Talebiniz Alındı! ID: {sid}"); st.balloons()

# --- 📄 3. SAYFA: EVRAK BİLGİSİ ---
elif st.session_state.sayfa == "evrak_ekrani":
    st.markdown("### 📄 Gerekli Evraklar Rehberi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    mud_sec = st.selectbox("Lütfen Müdürlük Seçiniz:", ["Seçiniz..."] + list(EVRAK_DATABANK.keys()))
    if mud_sec != "Seçiniz...":
        islem_sec = st.selectbox("Yapmak istediğiniz işlemi seçiniz:", list(EVRAK_DATABANK[mud_sec].keys()))
        if islem_sec:
            st.info(f"📋 **{islem_sec}** işlemi için istenen belgeler:")
            belgeler = EVRAK_DATABANK[mud_sec][islem_sec]
            for b in belgeler:
                st.write(f"✅ {b}")
            st.caption("Not: Belgelerin aslı ve fotokopisi ile birlikte başvurmanız önerilir.")

# --- 🔍 4. SAYFA: SORGULAMA ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sorgu = st.text_input("E-posta Adresiniz:")
    s_sorgu = st.text_input("Sohbet Şifreniz:", type="password")
    if m_sorgu:
        df_s = veri_yukle()
        if not df_s.empty:
            res = df_s[df_s["E-posta"] == m_sorgu]
            if not res.empty: st.markdown("#### 📋 Şikayetleriniz"), st.table(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
        df_m = mesaj_yukle()
        kendi_msgs = df_m[(df_m["Gonderen"] == m_sorgu) & (df_m["Sifre"].astype(str) == str(s_sorgu))]
        if not kendi_msgs.empty:
            birim_list = kendi_msgs["Mudurluk"].unique().tolist()
            sec_b = st.radio("Sohbeti Aç:", birim_list, horizontal=True)
            for idx, r in kendi_msgs[kendi_msgs["Mudurluk"] == sec_b].iterrows():
                with st.chat_message("user"):
                    st.write(r['Mesaj'])
                    if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(None, r['Dosya_Adi'], "Sizin Dosyanız"), unsafe_allow_html=True)
                if r['Cevap'] != "Bekleniyor":
                    with st.chat_message("assistant"):
                        st.write(r['Cevap'])
                        if r['Mudurluk_Dosya'] != "Yok": st.write(f"📎 Birim Dosyası: {r['Mudurluk_Dosya']}")

# --- 🏢 5. SAYFA: İLETİŞİM ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlükle Mesajlaşma")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("msg_form"):
        k_mud = st.selectbox("Birim:", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Şifre Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Belge Ekle:")
        if st.form_submit_button("Gönder"):
            fn = "Yok"
            if k_file:
                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                fn = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(k_file.getbuffer())
            yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
            pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
            st.success("İletildi!")

# --- 🏢 MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_b = st.selectbox("Birim:", tum_birimler, key="adm_birim")
    adm_s = st.text_input("Şifre:", type="password", key="adm_pass")
    if adm_s == "1234":
        t1, t2 = st.tabs(["Kayıtlar", "💬 Sohbetler"])
        with t2:
            df_m = mesaj_yukle()
            birim_m = df_m[df_m["Mudurluk"] == adm_b]
            ara_v = st.text_input("🔍 Vatandaş Ara:")
            v_list = [v for v in birim_m["Gonderen"].unique() if ara_v.lower() in str(v).lower()]
            if v_list:
                v_sec = st.selectbox("Seç:", v_list)
                v_gecmis = birim_m[birim_m["Gonderen"] == v_sec]
                for idx, r in v_gecmis.iterrows():
                    with st.container(border=True):
                        st.write(f"👤 **Vatandaş:** {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok":
                            yol = os.path.join("yuklenen_belgeler", str(r['Dosya_Adi']))
                            if os.path.exists(yol):
                                with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(r['Dosya_Adi']), "Vatandaş Belgesi"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Yanıt: {r['Cevap']}")
                y_not = st.text_area("Yanıt Yazın:", key="ans_adm")
                y_file = st.file_uploader("Dosya Gönder:", key="file_adm")
                if st.button("Yanıtı Gönder"):
                    df_m.at[v_gecmis.index[-1], "Cevap"] = y_not
                    df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                    st.success("İletildi!"); st.rerun()
