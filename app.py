import streamlit as st
import requests
from bs4 import BeautifulSoup
from googlesearch import search

# הגדרות עיצוב ודף
st.set_page_config(page_title="מפרט רכב iCar", page_icon="🚗")

# RTL CSS
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

def get_car_info_from_gov(plate):
    """גרסה 3: חיפוש רחב במאגר הממשלתי"""
    plate = "".join(filter(str.isdigit, str(plate)))
    if not plate: return None

    # ננסה את שני המאגרים המרכזיים אחד אחרי השני
    resources = [
        '43265886-932d-4f7d-ba32-4740e5502b66', # רכב פעיל
        '053ad4d1-c116-433c-a27b-023568858be'  # רכב פרטי ומסחרי
    ]
    
    for res_id in resources:
        url = f"https://data.gov.il/api/3/action/datastore_search?resource_id={res_id}&q={plate}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                records = data.get('result', {}).get('records', [])
                for r in records:
                    # וידוא התאמה למספר הרישוי (המאגר מחזיר לעיתים תוצאות דומות)
                    if str(r.get('mispar_rechev')) == plate:
                        return r
        except:
            continue
    return None

def scrape_icar_specs(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        specs = {"מנוע": {}, "מידות": {}, "בטיחות": [], "מולטימדיה": [], "נוחות": []}
        
        for group in soup.select('.spec-group'):
            title = group.select_one('.group-title').text.strip() if group.select_one('.group-title') else ""
            for row in group.select('.spec-item'):
                label = row.select_one('.label').text.strip()
                val_div = row.select_one('.value')
                val_text = val_div.text.strip()
                is_checked = "V" in val_text or val_div.find('i') or "יש" in val_text
                
                if any(x in label for x in ["נפח", "תיבת הילוכים", "הספק", "סוג מנוע", "תאוצה"]):
                    specs["מנוע"][label] = val_text
                elif any(x in label for x in ["אורך", "רוחב", "גובה", "בסיס גלגלים", "תא מטען"]):
                    specs["מידות"][label] = val_text
                elif is_checked:
                    if "בטיחות" in title: specs["בטיחות"].append(label)
                    elif "מולטימדיה" in title or "תקשורת" in title: specs["מולטימדיה"].append(label)
                    else: specs["נוחות"].append(label)
        return specs
    except: return None

# UI
st.title("🚗 מפרט רכב מלא")
plate_input = st.text_input("הכנס מספר רישוי:", placeholder="למשל: 32059903")

if plate_input:
    with st.spinner('בודק נתונים...'):
        car = get_car_info_from_gov(plate_input)
        if car:
            # שליפת שדות עם תמיכה בשמות שונים של עמודות במאגרים שונים
            make = car.get('tozar', car.get('tozar_rechev', ''))
            model = car.get('kinuy_mishari', '')
            trim = car.get('ramat_gimur', '')
            year = car.get('shnat_yitzur', '')
            
            full_name = f"{make} {model} {trim} {year}"
            st.success(f"**רכב זוהה:** {full_name}")
            
            # חיפוש iCar
            try:
                found_url = next(search(f"site:icar.co.il {full_name} מפרט", num_results=1, lang="he"), None)
                if found_url:
                    data = scrape_icar_specs(found_url)
                    if data:
                        t1, t2, t3 = st.tabs(["📊 טכני", "🛡️ בטיחות", "💎 אבזור"])
                        with t1:
                            c1, c2 = st.columns(2)
                            with c1:
                                st.write("### מנוע")
                                for k,v in data["מנוע"].items(): st.write(f"**{k}:** {v}")
                            with c2:
                                st.write("### מידות")
                                for k,v in data["מידות"].items(): st.write(f"**{k}:** {v}")
                        with t2:
                            st.write("### בטיחות")
                            st.write(", ".join(data["בטיחות"]) if data["בטיחות"] else "אין מידע")
                        with t3:
                            st.write("### אבזור")
                            st.write(", ".join(data["נוחות"] + data["מולטימדיה"]) if (data["נוחות"] or data["מולטימדיה"]) else "אין מידע")
                    else: st.error("לא הצלחנו לקרוא את המפרט מהדף.")
                else: st.error("לא נמצא דף ב-iCar.")
            except: st.error("שגיאה בחיפוש הנתונים.")
        else:
            st.error("מספר הרישוי לא נמצא במאגר הממשלתי. וודא שהמספר תקין.")

st.markdown("<br><br><br><div class='footer'>המידע מ-iCar ובאחריותם בלבד. | קרדיט ליואב מורד על בניית האתר.</div>", unsafe_allow_html=True)
