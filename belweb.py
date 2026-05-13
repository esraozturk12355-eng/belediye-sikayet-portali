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
    if not os.path.exists(dosya_yolu): return f"⚠️ Dosya Bulunamadı"
    with open(dosya_yolu, "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold;">📩 {etiket}</a>'

# --- 📚 10 MÜDÜRLÜK VE TÜM İŞLEMLER ---
EVRAK_REHBERI_DICT = {
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Nüfus Cüzdanı Aslı", "Sağlık Raporu", "4 Adet Fotoğraf", "İkametgah Belgesi", "Bekarlık Belgesi"],
        "Asker Ailesi Yardımı": ["Askerlik Belgesi", "Nüfus Kayıt Örneği", "Fakirlik Belgesi", "Kira Kontratı", "Kimlik Fotokopisi"],
        "Encümen Kararı Örneği": ["Dilekçe", "Kimlik Fotokopisi", "Karar No/Tarih Bilgisi", "Tapu Kaydı", "Vekaletname"],
        "Arşiv Belge Talebi": ["Başvuru Dilekçesi", "Tapu Fotokopisi", "Vergi Borcu Yoktur Yazısı", "Kimlik", "Harç Makbuzu"],
        "Genel Dilekçe İşlemleri": ["İmzalı Dilekçe", "Kimlik Fotokopisi", "İletişim Bilgileri", "Adres Beyanı", "Ek Belgeler"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol Onarım Talebi": ["Hasar Fotoğrafı", "Konum Bilgisi", "Dilekçe", "Muhtar Onayı", "İletişim Bilgisi"],
        "Kaldırım Hasarı": ["Fotoğraf", "İkametgah", "Dilekçe", "Adres Bilgisi", "Kimlik Beyanı"],
        "Kazı Çalışma İzni": ["Altyapı Planı", "Çalışma Takvimi", "Emniyet Planı", "Harç Dekontu", "Taahhütname"],
        "Yağmur Suyu Hattı": ["Başvuru Dilekçesi", "Sokak Krokisi", "İmar Yazısı", "Tapu Bilgisi", "Nüfus Kayıt Örneği"],
        "Asfalt Kaplama": ["Muhtarlık Yazısı", "Talep Dilekçesi", "Yol Genişlik Raporu", "Sakinlerin İmzası", "Hizmet Dekontu"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma Ruhsatı": ["Tapu/Kira Kontratı", "Vergi Levhası", "İtfaiye Raporu", "Oda Kaydı", "Ustalık Belgesi"],
        "Pazar Yeri Tahsisi": ["Pazarcı Belgesi", "Sabıka Kaydı", "İkametgah", "2 Fotoğraf", "Borcu Yoktur Yazısı"],
        "Gürültü Şikayeti": ["Dilekçe", "Olay Yeri Adresi", "Zaman Bilgisi", "Kimlik Beyanı", "Varsa Video/Ses Kaydı"],
        "Kaldırım İşgali": ["Ruhsat Fotokopisi", "Alan Krokisi", "Güncel Vergi Borcu", "Kimlik Fotokopisi", "Kullanım İzni"],
        "Seyyar Satıcı Şikayeti": ["Konum Bilgisi", "Şikayet Saati", "Dilekçe", "Fotoğraf", "İletişim Numarası"]
    },
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Güncel Tapu", "Mimari Proje", "İmar Durum Belgesi", "Zemin Etüdü", "Müellif Taahhüdü"],
        "İskan (Yapı Kullanma)": ["Enerji Kimlik Belgesi", "SGK İlişiksiz Belgesi", "İtfaiye Uygunluk", "Asansör Tescili", "Sığınak Raporu"],
        "Numarataj İşlemleri": ["Tapu Fotokopisi", "Yapı Ruhsatı", "İmza Sirküleri", "Bina Fotoğrafı", "Kadastro Çapı"],
        "İmar Durum Sorgulama": ["Dilekçe", "Tapu Kaydı", "Kadastro Çapı", "Koordinat Özet Çizelgesi", "Harç Makbuzu"],
        "Kaçak Yapı İhbarı": ["İhbar Dilekçesi", "Adres Bilgisi", "Fotoğraflar", "Kimlik Bilgileri", "Konum Verisi"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sokak Hayvanı Tedavi": ["Başvuru Formu", "Konum Bilgisi", "İhbarcı Kimliği", "Fotoğraf", "İletişim"],
        "Sahipli Hayvan Kaydı": ["Hayvan Pasaportu", "Aşı Karnesi", "Çip Numarası", "Sahip Kimliği", "İkametgah Belgesi"],
        "İlaçlama Talebi": ["Dilekçe", "Adres Beyanı", "Alan Metrekaresi", "Kimlik", "Yerleşim Yeri Belgesi"],
        "Kısırlaştırma": ["Sağlık Karnesi", "Sahip Kimlik Kartı", "Randevu Formu", "Taahhütname", "İkametgah"],
        "Yaralı Hayvan Bildirimi": ["Olay Yeri Fotoğrafı", "Konum", "Beyan Formu", "İletişim", "Bölge Bilgisi"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Emlak Bildirim Formu", "Rayiç Bedel Yazısı", "İskan Belgesi"],
        "Borç Yapılandırma": ["Dilekçe", "Kimlik Fotokopisi", "Eski Makbuzlar", "İmza Sirküleri", "Yapılandırma Formu"],
        "Rayiç Bedel Belgesi": ["Tapu Kaydı", "Kimlik", "Belediye Borcu Yoktur Yazısı", "Vekaletname", "Harç Dekontu"],
        "Ödeme Problemleri": ["Makbuz Örneği", "Dilekçe", "Banka Dekontu", "Kimlik", "Ekstre Bilgisi"],
        "Çevre Temizlik Vergisi": ["Kira Kontratı", "Vergi Levhası", "Kimlik", "Tapu Bilgisi", "Adres Kaydı"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Taşınmaz Kiralama": ["Dilekçe", "Kimlik", "İmza Beyannamesi", "Teminat Dekontu", "Oda Kayıt Belgesi"],
        "Ecrimisil Ödemeleri": ["Ödeme Emri Belgesi", "Dilekçe", "Kimlik", "İlgili Yerin Krokisi", "Geçmiş Makbuzlar"],
        "Kamulaştırma Bilgisi": ["Tapu Kaydı", "Kimlik", "Dilekçe", "Veraset İlamı", "Vekaletname"],
        "Yer Tahsisi": ["Kurum Yazısı / Dilekçe", "Kimlik", "Faaliyet Belgesi", "Tüzük", "Proje Detayı"],
        "Gayrimenkul Satış": ["Şartname", "Geçici Teminat", "Kimlik", "İkametgah", "Yetki Belgesi"]
    },
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {
        "Geri Dönüşüm Kutusu": ["Talep Dilekçesi", "Site/Apartman Karar Örneği", "Konum Bilgisi", "Kimlik", "Adres Beyanı"],
        "Atık Yağ Toplama": ["Adres", "Miktar Bilgisi", "Dilekçe", "İletişim Numarası", "Kap Kapasite Bilgisi"],
        "Elektronik Atık": ["Atık Listesi", "Konum", "Dilekçe", "Kimlik", "Randevu Tarihi"],
        "Sıfır Atık Eğitimi": ["Başvuru Yazısı", "Katılımcı Sayısı", "Konu Başlıkları", "Kurum Bilgisi", "İletişim"],
        "Kompost Üretim Bilgi": ["Başvuru", "Adres", "Bahçe/Alan Bilgisi", "Kimlik", "İletişim"]
    },
    "Destek Hizmetleri Müdürlüğü": {
        "İhale Dosyası Alımı": ["Vezne Makbuzu", "İmza Sirküleri", "Kimlik Fotokopisi", "Yetki Belgesi", "Oda Kaydı"],
        "Tedarikçi Kaydı": ["Vergi Levhası", "Ticaret Sicil Gazetesi", "İmza Sirküleri", "Banka Bilgileri", "Faaliyet Belgesi"],
        "Satın Alma Talebi": ["Teknik Şartname", "Piyasa Araştırma Formu", "Birim Onayı", "Bütçe Ödeneği Yazısı", "Dilekçe"],
        "Doğrudan Temin": ["Fiyat Teklifi", "Firma Bilgi Formu", "Vergi Borcu Yoktur Yazısı", "SGK Borcu Yoktur", "Kimlik"],
        "Hizmet Alımı": ["İş Deneyim Belgesi", "Sözleşme Taslağı", "Onay Belgesi", "Birim Yazısı", "Firma Evrakları"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Riskli Yapı Tespiti": ["Tapu Aslı", "Nüfus Kayıt Örneği", "Belediye Borcu Yoktur", "Dilekçe", "Bina Krokisi"],
        "Yıkım Kararı Sorgulama": ["Dilekçe", "Kimlik", "Tapu Fotokopisi", "Encümen Kararı Örneği", "Harç Makbuzu"],
        "Bina Güvenlik Riski": ["İhbar Dilekçesi", "Fotoğraflar", "Adres Bilgisi", "Kimlik", "İletişim"],
        "İskan Kontrolü": ["Yapı Ruhsatı", "Müellif Raporu", "İtfaiye Onayı", "SGK Yazısı", "Kimlik"],
        "Statik Rapor Talebi": ["Tapu Kaydı", "Dilekçe", "Bina Kimlik Numarası", "Harç Dekontu", "Kimlik"]
    }
}
tum_birimler = sorted(list(EVRAK_REHBERI_DICT.keys()))

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
        st.info("### 👤 Vatandaş Portalı\nAkıllı Asistan ile işlemlerinizi hızla halledin.")
        if st.button("Vatandaş Girişi", use_container_width=True):
            st.session_state.portal_modu = "vatandas"; st.rerun()
    with cm:
        st.success("### 🏢 Müdürlük Paneli\nYetkili girişi yaparak sistemi yönetin.")
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
            det = st.text_area("Detaylar")
            if st.button("Talebi Gönder"):
                if ad and soyad and re.match(EMAIL_PATTERN, ep, re.IGNORECASE) and re.match(PHONE_PATTERN, tel):
                    sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                    pd.DataFrame([{"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel, "Müdürlük": mud_sec, "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success("✅ Talebiniz iletildi!"); time.sleep(2); st.rerun()

    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Takip ve Sorgulama")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.container(border=True):
            arama = st.text_input("E-posta veya Telefon")
            sf = st.text_input("Sohbet Şifreniz", type="password")
            if arama:
                temiz = tel_temizle(arama); df_t = veri_yukle()
                if not df_t.empty:
                    res_t = df_t[(df_t["E-posta"] == arama) | (df_t["Telefon"].apply(tel_temizle) == temiz)]
                    if not res_t.empty: st.markdown("#### 📋 Talepleriniz"), st.table(res_t[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
                df_m = mesaj_yukle()
                if not df_m.empty:
                    k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == temiz)) & (df_m["Sifre"].astype(str) == str(sf))]
                    if not k_msg.empty:
                        st.divider(); b_sec = st.radio("Birim:", k_msg["Mudurluk"].unique(), horizontal=True)
                        for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                            with st.chat_message("user"):
                                st.write(r['Mesaj'])
                                if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Dosyanız"), unsafe_allow_html=True)
                            if r['Cevap'] != "Bekleniyor":
                                with st.chat_message("assistant"):
                                    st.write(r['Cevap'])
                                    if r['Mudurluk_Dosya'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("belediye_belgeleri", str(r['Mudurluk_Dosya'])), str(r['Mudurluk_Dosya']), "Belediye Evrağı"), unsafe_allow_html=True)
                        with st.expander("📥 Yanıt Yaz"):
                            with st.form("q_rep"):
                                rm = st.text_area("Mesaj"); rf = st.file_uploader("Belge")
                                if st.form_submit_button("Yanıtı Gönder"):
                                    pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": current.iloc[0]["Ad"], "Soyad": current.iloc[0]["Soyad"], "Gonderen": arama, "Telefon": temiz, "Sifre": sf, "Mudurluk": b_sec, "Mesaj": rm, "Dosya_Adi": "Yok", "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                                    st.success("✅ İletildi!"); time.sleep(2); st.rerun()

    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Yeni Sohbet")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.form("init_chat"):
            c1, c2 = st.columns(2)
            u_ad = c1.text_input("Ad"); u_soyad = c2.text_input("Soyad")
            u_mail = c1.text_input("E-posta"); u_tel = c2.text_input("Telefon")
            u_pass = st.text_input("Şifre Belirle", type="password"); u_mud = st.selectbox("Birim", tum_birimler); u_msg = st.text_area("Mesaj"); u_f = st.file_uploader("Belge")
            if st.form_submit_button("Sohbeti Başlat"):
                if u_ad and u_soyad and re.match(EMAIL_PATTERN, u_mail) and re.match(PHONE_PATTERN, u_tel):
                    st.success("✅ İletildi!"); time.sleep(2); st.rerun()

    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Evrak Rehberi & İşlem Kılavuzu")
        if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        m_s = st.selectbox("Müdürlük Seçiniz", tum_birimler)
        if m_s in EVRAK_REHBERI_DICT:
            islem = st.radio("İşlem Seçiniz:", list(EVRAK_REHBERI_DICT[m_s].keys()))
            with st.container(border=True):
                st.markdown(f"#### 📁 {islem} İçin Gerekli Evraklar")
                for e in EVRAK_REHBERI_DICT[m_s][islem]: st.markdown(f"- ✅ {e}")
        else: st.info("Bu birim için evrak rehberi yakında eklenecektir.")

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
                            df_t.at[idx[0], "Müdürlük"] = ys; df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig"); st.success("Güncellendi!"); time.sleep(1); st.rerun()
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
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Vatandaşın Dosyası"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Cevabınız: {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Cevap"); f = st.file_uploader("Belge")
                    if st.form_submit_button("Yanıtla"):
                        df_m.at[vg.index[-1], "Cevap"] = a; df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig"); st.success("İletildi!"); time.sleep(1.5); st.rerun()
