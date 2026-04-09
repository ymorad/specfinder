import streamlit as st
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time

# הגדרות דף
st.set_page_config(page_title="מפרט רכב iCar - יואב מורד", page_icon="🚗")

# עיצוב RTL
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stText"], div[data-testid="stMarkdownContainer"] p { text-align: right; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #555; text-align: center;
        padding: 10px; font-size: 14px; border-top: 1px solid #ddd; z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

def get_car_info(plate):
    """שליפת נתונים מהממשלה עם Headers של דפדפן כדי למנוע חסימה"""
    plate = "".join(filter(str.isdigit, str(plate)))
    if not plate: return None
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    resource_id = '43265886-932d-4f7d-ba32-4740e5502b66' # מאגר רכב פעיל
    url = f"https://data.gov.il/api/3/action/datastore_search?resource_id={resource_id}&q={plate}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        records = data.get('result', {}).get('records', [])
        for r in records:
            if str(r.get('mispar_rechev')) == plate:
                return r
    except:
        return None
    return None

def scrape_icar(url):
    """סריקת מפרט מ-iCar"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        specs = {"מנוע": {}, "מידות": {}, "בטיחות": [], "אבזור": []}
        
        for group in soup.select('.spec-group'):
            title = group.select_one('.group-title').text.strip() if group.select_one('.group-title') else ""
            for row in group.select('.spec-item'):
                label = row.select_one('.label').text.strip()
                val_div = row.select_one('.value')
                is_checked = "V" in val_div.text or val_div.find('i')
                
                if any(x in label for x in ["נפח", "הילוכים", "הספק", "תאוצה"]):
                    specs["מנוע"][label] = val_div.text.strip()
                elif any(x in label for x in ["אורך", "רוחב", "גובה", "בסיס גלגלים"]):
                    specs["מידות"][label] = val_div.text.strip()
                elif is_checked:
                    if "בטיחות" in title: specs["בטיחות"].append(label)
                    else: specs["אבזור"].append(label)
        return specs
    except: return None

# ממשק משתמש
st.title("🚗 בודק מפרט רכב")
plate_input = st.text_input("הכנס מספר רישוי:", key="plate_input")

if plate_input:
    car = get_car_info(plate_input)
    if car:
        name = f"{car.get('tozar', '')} {car.get('kinuy_mishari', '')} {car.get('ramat_gimur', '')} {car.get('shnat_yitzur', '')}"
        st.success(f"**נמצא רכב:** {name}")
        
        # ניסיון חיפוש אוטומטי
        search_query = f"site:icar.co.il {name} מפרט"
        found_url = None
        
        try:
            # הוספת delay קטן כדי לא להיחסם בגוגל
            time.sleep(1)
            results = list(search(search_query, num_results=1, lang="he"))
            if results: found_url = results[0]
        except:
            st.warning("חיפוש אוטומטי נחסם זמנית. לחץ על הקישור למטה כדי למצוא את המפרט ב-iCar:")
            st.markdown(f"[חפש את הדגם ב-iCar באופן ידני](https://www.google.com/search?q={search_query.replace(' ', '+')})")

        if found_url:
            data = scrape_icar(found_url)
            if data:
                t1, t2, t3 = st.tabs(["📊 מפרט", "🛡️ בטיחות", "💎 אבזור"])
                with t1:
                    c1, c2 = st.columns(2)
                    with c1:
                        for k,v in data["מנוע"].items(): st.write(f"**{k}:** {v}")
                    with c2:
                        for k,v in data["מידות"].items(): st.write(f"**{k}:** {v}")
                with t2: st.write(", ".join(data["בטיחות"]) if data["בטיחות"] else "אין מידע")
                with t3: st.write(", ".join(data["אבזור"]) if data["אבזור"] else "אין מידע")
                st.caption(f"מקור: {found_url}")
    else:
        st.error("המספר לא נמצא במאגר הממשלתי. וודא שהזנת מספר תקין (ללא רווחים).")

st.markdown("<br><br><br><div class='footer'>המידע מ-iCar ובאחריותם בלבד. | קרדיט ליואב מורד על בניית האתר.</div>", unsafe_allow_html=True)
