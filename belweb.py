import streamlit as st
import pandas as pd
import os
import re
import base64
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Şikayet Portalı", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

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
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Uygunluk Raporu", "Oda Kayıt Belgesi"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe veya Fotoğraflı Kanıt"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası"]
    }
}

# --- DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:8px 16px; border-radius:4px;">📩 {dosya_adi} İndir</a>'

# --- SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 6]) 
with c1:
    logo_dosyasi = "logo.jfif"
    if os.path.exists(logo_dosyasi): st.image(logo_dosyasi, width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Şikayet Yönetim Portalı")

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
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

# MÜDÜRLÜKLER
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

st.divider()

# --- 🤖 BÖLÜM 1: AKILLI ASİSTAN KATMANI ---
with st.expander("🤖 Akıllı Asistan ile Konuşun (Yardımcı Rehber)", expanded=True):
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ben belediye asistanınız. 😊 Size şikayet oluşturma, sorgulama veya evrak bilgisi konusunda rehberlik edebilirim. Ne yapmak istersiniz?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("---")
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    if c_btn1.button("📝 Şikayet Nasıl Oluşturulur?"):
        st.session_state.messages.append({"role": "assistant", "content": "Şikayet oluşturmak için hemen alttaki **'📝 Yeni Şikayet Oluştur'** sekmesini kullanabilirsiniz."})
        st.rerun()
    if c_btn2.button("🔍 Sorgulama Nereden Yapılır?"):
        st.session_state.messages.append({"role": "assistant", "content": "Şikayetlerinizi takip etmek için alttaki **'🔍 Şikayetlerimi Görüntüle'** sekmesine geçebilirsiniz."})
        st.rerun()
    if c_btn3.button("📄 Evrak Bilgisi Al"):
        st.session_state.messages.append({"role": "assistant", "content": "Evrak bilgileri için alttaki **'📄 Evrak Rehberi'** sekmesini inceleyebilirsiniz."})
        st.rerun()

    if prompt := st.chat_input("Sorunuzu buraya yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        if any(x in p_low for x in ["şikayet", "sikayet", "oluştur"]):
            st.session_state.messages.append({"role": "assistant", "content": "Şikayet oluşturmak için lütfen alttaki form sekmesini kullanın."})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Size şikayet, sorgulama ve evraklar konusunda yardımcı olabilirim."})
        st.rerun()

st.divider()

# --- ANA SAYFA SEKMELERİ ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle", "📄 Evrak Rehberi", "🏢 Müdürlüğe Belge Gönder"])

# --- TAB 1: YENİ ŞİKAYET ---
with tab1:
    st.markdown("### 📝 Yeni Şikayet Formu")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.text_input("Adınız", key="ad_yeni")
        eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
        is_email_valid = False
        if eposta != "": 
            if re.match(email_pattern, eposta, re.IGNORECASE):
                st.success("E-posta formatı geçerli. ✅"); is_email_valid = True
            else: st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")

    with c2: 
        soyad = st.text_input("Soyadınız", key="soyad_yeni")
        telefon_input = st.text_input("Telefon Numaranız", key="tel_yeni")
    
    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_yeni")
    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi, key="tur_yeni")
    detay = st.text_area("Şikayet Detayı", key="detay_yeni")
    
    if st.button("Şikayeti Kaydet"):
        if ad and soyad and eposta and is_email_valid and telefon_input:
            temiz_tel = tel_temizle(telefon_input)
            df_mevcut = veri_yukle()
            yeni_sira_no = 1
            if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns and "Sıra_No" in df_mevcut.columns:
                birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                if not birim_kayitlari.empty: yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
            
            sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
            yeni_kayit = {
                "ID": sikayet_id, "Sıra_No": yeni_sira_no, 
                "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu,
                "Detay": detay.replace(",", " "), "Durum": "İnceleniyor",
                "Belediye_Cevabi": "Henüz cevaplanmadı"
            }
            pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"✅ Şikayetiniz başarıyla alınmıştır. Takip ID: {sikayet_id}"); st.balloons()
        else: st.error("Lütfen formu eksiksiz doldurunuz.")

# --- TAB 2: ŞİKAYET GÖRÜNTÜLEME ---
with tab2:
    st.markdown("### 🔍 Şikayet ve Mesaj Sorgulama")
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz", key="sorgu_input")
    s_sifre = st.text_input("Mesaj Şifreniz (Varsa):", type="password", key="s_sifre")
    if arama:
        temiz_arama = tel_temizle(arama)
        df = veri_yukle()
        if not df.empty:
            df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
            if not sonuclar.empty:
                st.info("Kayıtlarınız:")
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
        
        # Mesaj yanıtları
        df_m = mesaj_yukle()
        if not df_m.empty:
            kendi = df_m[(df_m["Gonderen"] == arama) & (df_m["Sifre"].astype(str) == str(s_sifre))]
            if not kendi.empty:
                st.markdown("#### 💬 Gelen Yanıtlar")
                st.dataframe(kendi[["Tarih", "Mudurluk", "Mesaj", "Cevap"]])

# --- TAB 3: EVRAK REHBERİ ---
with tab3:
    st.markdown("### 📄 Müdürlük Evrak Listeleri")
    m_s = st.selectbox("Müdürlük Seçin:", ["Seçiniz..."] + sorted(list(EVRAK_REHBERI.keys())))
    if m_s != "Seçiniz...":
        i_s = st.selectbox("İşlem Seçin:", list(EVRAK_REHBERI[m_s].keys()))
        for b in EVRAK_REHBERI[m_s][i_s]: st.write(f"✅ {b}")

# --- TAB 4: MÜDÜRLÜĞE BELGE GÖNDER ---
with tab4:
    st.markdown("### 🏢 Belge Gönderim Sistemi")
    with st.form("direkt_iletisim", clear_on_submit=True):
        k_mud = st.selectbox("İletişime Geçilecek Müdürlük:", tum_birimler)
        k_mail = st.text_input("E-posta Adresiniz:")
        k_sifre = st.text_input("Şifre Belirleyin:", type="password")
        k_mesaj = st.text_area("Mesajınız:")
        k_dosya = st.file_uploader("Belge Seçin:")
        if st.form_submit_button("Gönder"):
            if k_mail and k_sifre and k_mesaj:
                dosya_adi = "Yok"
                if k_dosya:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    dosya_adi = f"{datetime.now().strftime('%H%M%S')}_{k_dosya.name}"
                    with open(os.path.join("yuklenen_belgeler", dosya_adi), "wb") as f: f.write(k_dosya.getbuffer())
                
                yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_mesaj.replace(",","."), "Dosya_Adi": dosya_adi, "Cevap": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("Talebiniz iletildi!")
            else: st.error("Lütfen tüm alanları doldurun.")

# --- MÜDÜRLÜK PANELİ (Orijinal Yapı) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2: sifre_adm = st.text_input("Şifre:", type="password", key="adm_pass")

    if sifre_adm == "1234":
        adm_t1, adm_t2 = st.tabs(["📋 Şikayet Yönetimi", "💬 Mesajlar & Belgeler"])
        with adm_t1:
            df_adm = veri_yukle()
            if not df_adm.empty:
                filtreli = df_adm[df_adm["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
                if not filtreli.empty:
                    st.dataframe(filtreli[["Sıra_No", "ID", "Tarih", "Ad", "Soyad", "Telefon", "Durum", "Detay", "Belediye_Cevabi"]])
                    secilen_id = st.selectbox("İşlem Yapılacak ID Seçiniz:", filtreli["ID"].tolist(), key="islem_id")
                    ci1, ci2 = st.columns(2)
                    with ci1:
                        yeni_durum = st.selectbox("Durum:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"])
                        yonlendir = st.selectbox("Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim))
                    with ci2: cevap_notu = st.text_area("Cevap:")
                    if st.button("Onayla"):
                        idx = df_adm[df_adm["ID"] == secilen_id].index
                        df_adm.at[idx[0], "Durum"] = yeni_durum
                        df_adm.at[idx[0], "Müdürlük"] = yonlendir
                        df_adm.at[idx[0], "Belediye_Cevabi"] = cevap_notu
                        df_adm.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.success("Güncellendi!"); st.rerun()
        
        with adm_t2:
            df_m = mesaj_yukle()
            if not df_m.empty:
                b_msj = df_m[df_m["Mudurluk"] == admin_birim]
                for i, row in b_msj.iterrows():
                    with st.container(border=True):
                        st.write(f"📧 **{row['Gonderen']}** | 💬 {row['Mesaj']}")
                        if row['Dosya_Adi'] != "Yok":
                            yol = os.path.join("yuklenen_belgeler", str(row['Dosya_Adi']))
                            if os.path.exists(yol):
                                with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(row['Dosya_Adi'])), unsafe_allow_html=True)
                        y_notu = st.text_area("Yanıtınız:", key=f"yanit_{i}")
                        if st.button("Yanıtı Gönder", key=f"btn_{i}"):
                            df_m.at[i, "Cevap"] = y_notu
                            df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                            st.success("Gönderildi!"); st.rerun()
