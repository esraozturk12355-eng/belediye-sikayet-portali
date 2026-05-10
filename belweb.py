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

# --- DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}">📩 {dosya_adi} İndir</a>'

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
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Uygunluk Raporu", "Oda Kayıt Belgesi"],
        "Pazar Yeri Tahsisi": ["Oda Kayıt Belgesi", "İkametgah", "Sabıka Kaydı"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe veya Fotoğraflı Kanıt"],
        "Alt Yapı Kazı İzni": ["Proje Onayı", "AYKOME İzin Belgesi", "Teminat Dekontu"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası"],
        "Sokak Hayvanı Tedavi Talebi": ["İhbar Dilekçesi", "Konum Bilgisi"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Taşınmaz Kiralama": ["İhale Şartnamesi", "Geçici Teminat Makbuzu", "İkametgah"],
        "Yer Tahsis Talebi": ["Kurumsal Yazı veya Şahsi Dilekçe", "Kullanım Amacı Belgesi"]
    },
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {
        "Atık Pil/Yağ Toplama Talebi": ["Adres Bilgisi", "İletişim Numarası"],
        "Geri Dönüşüm Konteynırı": ["Dilekçe", "Bina Sakinleri İmzası (Gerekirse)"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Yapı Denetim Onayı": ["Hakediş Raporu", "Laboratuvar Sonuçları"],
        "Kaçak Yapı İhbar": ["Ada/Parsel Bilgisi", "Olay Yeri Fotoğrafı"]
    },
    "Destek Hizmetleri Müdürlüğü": {
        "İhale Dosya Alımı": ["Firma İmza Sirküleri", "Vezne Makbuzu"],
        "Tedarikçi Kaydı": ["Vergi Levhası", "Ticaret Sicil Gazetesi"]
    }
}

BELEDİYE_İLETİŞİM = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "saat": "Hafta içi 08:30 - 17:30"
}

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"
if "messages" not in st.session_state: st.session_state.messages = []

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 6]) 
with c1:
    logo_dosyasi = "logo.jfif"
    if os.path.exists(logo_dosyasi): st.image(logo_dosyasi, width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş ve Yönetim Portalı")

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    if os.path.exists("mesajlar.csv"):
        try: return pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
        except: return pd.DataFrame(columns=["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"])
    return pd.DataFrame(columns=["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"])

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

st.divider()

# --- 🤖 BÖLÜM 1: AI ASİSTAN ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ondokuzmayıs Belediyesi Akıllı Asistanına hoş geldiniz. 😊 Size bugün nasıl yardımcı olabilirim?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### Hızlı İşlemler")
    r1c1, r1c2, r1c3 = st.columns(3)
    r2c1, r2c2 = st.columns(2)
    
    if r1c1.button("📝 Şikayet Oluştur"):
        st.session_state.messages.append({"role": "assistant", "content": "Anlaşıldı, sizi hemen şikayet formuna yönlendiriyorum..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r1c2.button("🔍 Şikayet Sorgulama"):
        st.session_state.messages.append({"role": "assistant", "content": "Sorgulama ekranına yönlendiriliyorsunuz..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r1c3.button("📄 Evrak & Bilgi Rehberi"):
        st.session_state.evrak_aktif = True

    if r2c1.button("🏢 Müdürlük ile İletişim & Belge Gönderimi"):
        st.session_state.sayfa = "iletisim_kanali"; st.rerun()

    if r2c2.button("📞 Belediye İletişim Bilgileri"):
        ans = f"📞 **Tel:** {BELEDİYE_İLETİŞİM['telefon']} \n📍 **Adres:** {BELEDİYE_İLETİŞİM['konum']} \n⏰ **Mesai:** {BELEDİYE_İLETİŞİM['saat']}"
        st.session_state.messages.append({"role": "assistant", "content": ans}); st.rerun()

    if "evrak_aktif" in st.session_state and st.session_state.evrak_aktif:
        st.write("---")
        st.markdown("#### 📂 Müdürlük Evrak Listeleri")
        m = st.selectbox("Lütfen Müdürlük seçiniz:", ["Seçiniz..."] + sorted(list(EVRAK_REHBERI.keys())))
        if m != "Seçiniz...":
            i = st.selectbox("İşlem seçiniz:", ["Seçiniz..."] + list(EVRAK_REHBERI[m].keys()))
            if i != "Seçiniz...":
                st.info(f"**{i}** için gerekli belgeler:")
                for b in EVRAK_REHBERI[m][i]: st.write(f"✅ {b}")
        if st.button("Rehberi Kapat"): del st.session_state.evrak_aktif; st.rerun()

    if prompt := st.chat_input("Mesajınızı yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        if any(x in p_low for x in ["şikayet", "sikayet", "oluştur"]):
            st.session_state.messages.append({"role": "assistant", "content": "Sizi hemen yönlendiriyorum..."})
            st.session_state.sayfa = "portal"; st.rerun()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Size şikayet kaydı veya evraklar konusunda yardımcı olabilirim."})
            st.rerun()

# --- 🏢 BÖLÜM: MÜDÜRLÜK İLETİŞİM KANALI ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlük İletişim ve Belge Gönderim Sistemi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.form("direkt_iletisim", clear_on_submit=True):
        k_mud = st.selectbox("İletişime Geçilecek Müdürlük:", tum_birimler)
        k_mail = st.text_input("E-posta Adresiniz:")
        k_sifre = st.text_input("Bu işlem için bir şifre belirleyiniz:", type="password", help="Yanıtı kontrol ederken bu şifreyi kullanacaksınız.")
        k_mesaj = st.text_area("Mesajınız veya Sorunuz:")
        k_dosya = st.file_uploader("Belge Yükle (PDF, PNG, JPG):")
        submit_msg = st.form_submit_button("Mesajı ve Belgeyi Gönder")
        
        if submit_msg:
            if k_mail and k_sifre and k_mesaj:
                temiz_msg = k_mesaj.replace(",", ".")
                dosya_adi = "Yok"
                if k_dosya:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    dosya_adi = f"{datetime.now().strftime('%H%M%S')}_{k_dosya.name}"
                    with open(os.path.join("yuklenen_belgeler", dosya_adi), "wb") as f:
                        f.write(k_dosya.getbuffer())

                yeni_mesaj = {
                    "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Gonderen": k_mail, "Sifre": k_sifre, "Mudurluk": k_mud, "Mesaj": temiz_msg,
                    "Dosya_Adi": dosya_adi, "Cevap": "Bekleniyor"
                }
                pd.DataFrame([yeni_mesaj]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("Talebiniz iletildi. Sorgulama ekranından şifrenizle takip edebilirsiniz.")
            else: st.error("Lütfen e-posta, şifre ve mesaj alanlarını doldurunuz.")

# --- 📝 BÖLÜM 2: ANA PORTAL ---
elif st.session_state.sayfa == "portal":
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"; st.rerun()

    tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

    with tab1:
        st.markdown("### 📝 Yeni Şikayet Formu")
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="ad_yeni")
            eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = False
            if eposta != "" and re.match(email_pattern, eposta, re.IGNORECASE):
                st.success("E-posta formatı geçerli. ✅"); is_email_valid = True
            elif eposta != "": st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")
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
                    "ID": sikayet_id, "Sıra_No": yeni_sira_no, "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                    "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu, "Detay": detay.replace(",", " "), 
                    "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"
                }
                pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"✅ Şikayet Alındı. ID: {sikayet_id}"); st.balloons()
            else: st.error("Lütfen formu eksiksiz doldurunuz.")

    with tab2:
        st.markdown("### 🔍 Şikayet Sorgulama")
        arama = st.text_input("E-posta veya Telefon numaranızı giriniz", key="sorgu_input")
        sorgu_sifre = st.text_input("İletişim Şifreniz (Mesaj yazdıysanız):", type="password")
        
        if arama:
            temiz_arama = tel_temizle(arama)
            df = veri_yukle()
            if not df.empty:
                df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
                sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
                if not sonuclar.empty:
                    st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            
            df_m = mesaj_yukle()
            if not df_m.empty:
                kendi_msj = df_m[(df_m["Gonderen"] == arama) & (df_m["Sifre"].astype(str) == sorgu_sifre)]
                if not kendi_msj.empty:
                    st.write("---")
                    st.markdown("#### 💬 Müdürlüklerden Gelen Yanıtlar")
                    st.dataframe(kendi_msj[["Tarih", "Mudurluk", "Mesaj", "Cevap"]])

# --- 🏢 MÜDÜRLÜK PANELİ ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2: sifre = st.text_input("Şifre:", type="password", key="adm_pass")

    if sifre == "1234":
        admin_tab1, admin_tab2 = st.tabs(["📋 Şikayetleri Yönet", "💬 Vatandaşla İletişim & Belgeler"])
        
        with admin_tab1:
            df_admin = veri_yukle()
            if not df_admin.empty:
                filtreli = df_admin[df_admin["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
                if not filtreli.empty:
                    st.dataframe(filtreli[["Sıra_No", "ID", "Tarih", "Ad", "Soyad", "Telefon", "Durum", "Detay", "Belediye_Cevabi"]])
                    st.write("---")
                    secilen_id = st.selectbox("İşlem Yapılacak ID Seçiniz:", filtreli["ID"].tolist(), key="islem_id")
                    ci1, ci2 = st.columns(2)
                    with ci1:
                        yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"], key="durum_up")
                        yonlendir = st.selectbox("Başka Birime Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim), key="yonlendir_up")
                    with ci2:
                        cevap_notu = st.text_area("Cevap Notu:", key="cevap_up")
                    if st.button("Değişiklikleri Onayla"):
                        idx = df_admin[df_admin["ID"] == secilen_id].index
                        if not idx.empty:
                            if df_admin.at[idx[0], "Müdürlük"] != yonlendir:
                                hedef = df_admin[df_admin["Müdürlük"] == yonlendir]
                                df_admin.at[idx[0], "Sıra_No"] = 1 if hedef.empty else hedef["Sıra_No"].max() + 1
                            df_admin.at[idx[0], "Durum"] = yeni_durum
                            df_admin.at[idx[0], "Müdürlük"] = yonlendir
                            df_admin.at[idx[0], "Belediye_Cevabi"] = cevap_notu
                            df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                            st.success("Kayıt güncellendi!"); st.rerun()

        with admin_tab2:
            st.markdown(f"#### {admin_birim} - Gelen Mesajlar ve Belgeler")
            df_m = mesaj_yukle()
            if not df_m.empty:
                birim_msj = df_m[df_m["Mudurluk"] == admin_birim]
                if not birim_msj.empty:
                    for index, row in birim_msj.iterrows():
                        with st.container(border=True):
                            st.write(f"**Gönderen:** {row['Gonderen']} | **Tarih:** {row['Tarih']}")
                            st.write(f"**Mesaj:** {row['Mesaj']}")
                            if row['Dosya_Adi'] != "Yok":
                                yol = os.path.join("yuklenen_belgeler", row['Dosya_Adi'])
                                if os.path.exists(yol):
                                    with open(yol, "rb") as f:
                                        st.markdown(dosya_indirme_linki(f.read(), row['Dosya_Adi']), unsafe_allow_html=True)
                            adm_yanit = st.text_area("Yanıtınız:", key=f"yanit_{index}")
                            if st.button("Yanıtı Gönder", key=f"btn_{index}"):
                                df_m.at[index, "Cevap"] = adm_yanit
                                df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                                st.success("Yanıt iletildi!"); st.rerun()
                else: st.info("Bu birime henüz direkt mesaj gelmemiş.")
