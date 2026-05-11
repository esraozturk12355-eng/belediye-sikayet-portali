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

# --- YENİ EKLENEN DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:8px 16px; border-radius:4px;">📩 {dosya_adi} İndir</a>'

# --- 📚 TÜM MÜDÜRLÜKLERİ KAPSAYAN EVRAK REHBERİ ---
EVRAK_REHBERI = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Kaydı", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi"],
        "Yapı Kullanma İzin Belgesi (İskan)": ["Enerji Kimlik Belgesi", "Sığınak Raporu", "SGK İlişiksiz Belgesi"],
        "Numarataj İşlemleri": ["Tapu Fotokopisi", "Yapı Ruhsatı", "Kimlik Fotokopisi"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Sağlık Raporu", "4 Adet Fotoğraf", "Nüfus Kayıt Örneği", "Kimlik Aslı"],
        "Encümen Kararı Örneği": ["Dilekçe", "İlgili Kararın Tarih ve Sayısı"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Kısıtlılık Belgesi (Varsa)"],
        "Rayiç Bedel Belgesi": ["Tapu Fotokopisi", "Borçsuzluk Yazısı", "İlgili Kişinin Kimliği"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "Oda Kaydı"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol Onarım Talebi": ["Konum Bilgisi", "Dilekçe"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi"]
    },
    "Destek Hizmetleri Müdürlüğü": {
        "İhale Dosya Alımı": ["Firma İmza Sirküleri", "Vezne Makbuzu"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Kiralama Talebi": ["İhale Şartnamesi", "İkametgah"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Kaçak Yapı İhbar": ["Ada/Parsel Bilgisi", "Fotoğraf"]
    },
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {
        "Atık Toplama": ["Adres Bilgisi", "İletişim"]
    }
}

# --- SESSION STATE (Sayfa Yönetimi) ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"]
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

sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + list(EVRAK_REHBERI.keys()))))

# --- ÜST BAŞLIK VE LOGO ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Yapay Zeka Destekli Vatandaş Portalı")

st.divider()

# --- 🤖 1. SAYFA: AKILLI ASİSTAN (ANA EKRAN) ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    st.write("Merhaba! Size nasıl yardımcı olabilirim? Lütfen yapmak istediğiniz işlemi seçiniz:")
    
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    if col1.button("📝 Talep ve Öneri Bildir", use_container_width=True):
        st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Talep Sorgulama", use_container_width=True):
        st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("📄 Evrak Bilgisi Al", use_container_width=True):
        st.session_state.sayfa = "evrak_ekrani"; st.rerun()
    if col4.button("🏢 Müdürlüğe Belge/Mesaj Gönder", use_container_width=True):
        st.session_state.sayfa = "iletisim_kanali"; st.rerun()
    if col5.button("📞 İletişim Bilgileri", use_container_width=True):
        st.info("📞 Tel: 0 (362) 511 44 88 \n📍 Adres: Pazar Mah. Atatürk Bulvarı No:165")

# --- 📝 2. SAYFA: TALEP VE ÖNERİ FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Talep ve Öneri Bildirim Formu")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız")
            eposta = st.text_input("E-posta Adresiniz")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = bool(re.match(email_pattern, eposta, re.IGNORECASE)) if eposta else False
        with c2:
            soyad = st.text_input("Soyadınız")
            tel_input = st.text_input("Telefon Numaranız")
        
        mud_sec = st.selectbox("İlgili Müdürlük", tum_birimler)
        tur_listesi = sikayet_turleri_dict.get(mud_sec, ["Genel Talep", "Diğer"])
        sikayet_turu = st.selectbox("Tür", tur_listesi)
        detay = st.text_area("Açıklama")
        
        if st.button("Talebi Kaydet"):
            if ad and soyad and is_email_valid and tel_input:
                df_mevcut = veri_yukle()
                yeni_sira_no = 1
                if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns and "Sıra_No" in df_mevcut.columns:
                    birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == mud_sec]
                    if not birim_kayitlari.empty: yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
                
                sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni = {"ID": sid, "Sıra_No": yeni_sira_no, "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(tel_input), "Müdürlük": mud_sec, "Tür": sikayet_turu, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}
                pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Talebiniz Alındı! Takip ID: {sid}"); st.balloons()
            else: st.error("Lütfen formu eksiksiz doldurun.")

# --- 🔍 3. SAYFA: SORGULAMA ---
elif st.session_state.sayfa == "sorgu_ekrani":
    st.markdown("### 🔍 Talep Sorgulama")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    arama = st.text_input("E-posta veya Telefon giriniz:")
    s_sifre = st.text_input("Mesaj Şifreniz (Varsa):", type="password")
    if arama:
        df_s = veri_yukle()
        if not df_s.empty:
            df_s['Telefon_Temiz'] = df_s['Telefon'].apply(tel_temizle)
            sonuclar = df_s[(df_s["E-posta"] == arama) | (df_s["Telefon_Temiz"] == tel_temizle(arama))]
            if not sonuclar.empty: st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
        
        df_m = mesaj_yukle()
        if not df_m.empty:
            kendi = df_m[(df_m["Gonderen"] == arama) & (df_m["Sifre"].astype(str) == str(s_sifre))]
            if not kendi.empty:
                st.write("---")
                st.markdown("#### 💬 Gelen Yanıtlar")
                st.dataframe(kendi[["Tarih", "Mudurluk", "Mesaj", "Cevap"]])

# --- 📄 4. SAYFA: EVRAK REHBERİ ---
elif st.session_state.sayfa == "evrak_ekrani":
    st.markdown("### 📄 Müdürlük Evrak Rehberi")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sec = st.selectbox("Müdürlük Seçin:", sorted(list(EVRAK_REHBERI.keys())))
    if m_sec:
        i_sec = st.selectbox("İşlem Seçin:", list(EVRAK_REHBERI[m_sec].keys()))
        st.info(f"**{i_sec}** için gerekli belgeler:")
        for b in EVRAK_REHBERI[m_sec][i_sec]: st.write(f"✅ {b}")

# --- 🏢 5. SAYFA: İLETİŞİM KANALI ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlük İletişim & Belge Gönderimi")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("msg_form", clear_on_submit=True):
        k_mud = st.selectbox("Birim:", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Sorgulama Şifresi Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Belge Seçin:")
        if st.form_submit_button("Gönder"):
            if k_mail and k_sifre and k_msg:
                d_adi = "Yok"
                if k_file:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    d_adi = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                    with open(os.path.join("yuklenen_belgeler", d_adi), "wb") as f: f.write(k_file.getbuffer())
                yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg.replace(",","."), "Dosya_Adi": d_adi, "Cevap": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("İletildi!")

# --- 🏢 MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2: sifre_adm = st.text_input("Şifre:", type="password", key="adm_pass")
    
    if sifre_adm == "1234":
        t1, t2 = st.tabs(["📋 Şikayet Yönetimi", "💬 Vatandaşla İletişim"])
        with t1:
            df_a = veri_yukle()
            if not df_a.empty and "Müdürlük" in df_a.columns:
                # KeyError: Sıra_No hatasını önleyen güvenli filtreleme
                if "Sıra_No" in df_a.columns:
                    filtreli = df_a[df_a["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
                else:
                    filtreli = df_a[df_a["Müdürlük"] == admin_birim]
                
                if not filtreli.empty:
                    st.dataframe(filtreli)
                    secilen_id = st.selectbox("İşlem Yapılacak ID:", filtreli["ID"].tolist())
                    c_up1, c_up2 = st.columns(2)
                    with c_up1:
                        y_durum = st.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi"])
                        y_birim = st.selectbox("Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim))
                    with c_up2: y_cevap = st.text_area("Yanıt Notu:")
                    if st.button("Güncelle"):
                        idx = df_a[df_a["ID"] == secilen_id].index
                        df_a.at[idx[0], "Durum"] = y_durum
                        df_a.at[idx[0], "Müdürlük"] = y_birim
                        df_a.at[idx[0], "Belediye_Cevabi"] = y_cevap
                        df_a.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.success("Başarılı!"); st.rerun()
        
        with t2:
            df_m = mesaj_yukle()
            if not df_m.empty:
                b_msj = df_m[df_m["Mudurluk"] == admin_birim]
                if not b_msj.empty:
                    for i, row in b_msj.iterrows():
                        with st.container(border=True):
                            st.write(f"📧 **Gönderen:** `{row['Gonderen']}`")
                            st.info(f"💬 **Mesaj:** {row['Mesaj']}")
                            if 'Dosya_Adi' in row and str(row['Dosya_Adi']) != "Yok":
                                yol = os.path.join("yuklenen_belgeler", str(row['Dosya_Adi']))
                                if os.path.exists(yol):
                                    with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(row['Dosya_Adi'])), unsafe_allow_html=True)
                            y_not = st.text_area("Vatandaşa Yanıtınız:", key=f"yanit_{i}")
                            if st.button("Yanıtı Gönder", key=f"btn_{i}"):
                                df_m.at[i, "Cevap"] = y_not
                                df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                                st.success("Gönderildi!"); st.rerun()
                else: st.info("Bu birime henüz mesaj gelmemiş.")
