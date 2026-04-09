import streamlit as st
import requests
from bs4 import BeautifulSoup
from googlesearch import search

# הגדרות עיצוב ודף
st.set_page_config(page_title="מפרט רכב iCar", page_icon="🚗")

# התאמת הכיוון לעברית (RTL) והגדרת Footer
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stText"], div[data-testid="stMarkdownContainer"] p { text-align: right; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #555;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-top: 1px solid #ddd;
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

def get_car_info_from_gov(plate):
    """שליפת נתונים ממאגר הממשלה - גרסה משופרת"""
    # ניקוי המספר מרווחים או מקפים
    plate = "".join(filter(str.isdigit, str(plate)))
    
    # שימוש במאגר 'רכב פעיל' שהוא המעודכן ביותר
    url = "https://data.gov.il/api/3/action/datastore_search"
    params = {
        'resource_id': '43265886-932d-4f7d-ba32-4740e5502b66',
        'q': plate
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        records = res.get('result', {}).get('records', [])
        
        # חיפוש התאמה מדויקת
        for record in records:
            if str(record.get('mispar_rechev')) == plate:
                return record
        return None
    except:
        return None

def scrape_icar_specs(url):
    """חילוץ המפרט המלא מדף iCar"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        specs = {
            "מנוע וביצועים": {}, 
            "מידות": {}, 
            "אבזור בטיחות": [], 
            "מולטימדיה": [], 
            "אבזור נוחות": []
        }
        
        for group in soup.select('.spec-group'):
            title = group.select_one('.group-title').text.strip() if group.select_one('.group-title') else ""
            
            for row in group.select('.spec-item'):
                label = row.select_one('.label').text.strip()
                val_div = row.select_one('.value')
                val_text = val_div.text.strip()
                
                is_checked = "V" in val_text or val_div.find('i') or "יש" in val_text
                
                if any(x in label for x in ["נפח", "תיבת הילוכים", "הספק", "סוג מנוע", "תאוצה", "מהירות"]):
                    specs["מנוע וביצועים"][label] = val_text
                elif any(x in label for x in ["אורך", "רוחב", "גובה", "בסיס גלגלים", "תא מטען", "משקל"]):
                    specs["מידות"][label] = val_text
                elif is_checked:
                    if "בטיחות" in title: specs["אבזור בטיחות"].append(label)
                    elif any(x in title for x in ["מולטימדיה", "תקשורת", "רדיו"]): specs["מולטימדיה"].append(label)
                    elif any(x in title for x in ["נוחות", "אבזור", "פנים"]): specs["אבזור נוחות"].append(label)
        return specs
    except:
        return None

# --- ממשק המשתמש ---
st.title("🚗 מחולל מפרט רכב מלא")
st.subheader("מבוסס נתוני משרד התחבורה ו-iCar")

plate_input = st.text_input("הכנס מספר רישוי:", placeholder="למשל: 32059903")

if plate_input:
    with st.spinner('מחפש במאגרי הממשלה...'):
        car_base = get_car_info_from_gov(plate_input)
        
        if car_base:
            # במאגר הזה השדות נקראים מעט אחרת
            make = car_base.get('tozar', '')
            model = car_base.get('kinuy_mishari', '')
            trim = car_base.get('ramat_gimur', '')
            year = car_base.get('shnat_yitzur', '')
            
            car_name = f"{make} {model} {trim} {year}"
            st.success(f"**רכב זוהה:** {car_name}")
            
            # חיפוש בגוגל
            search_query = f"site:icar.co.il {car_name} מפרט טכני"
            try:
                found_url = next(search(search_query, num_results=1, lang="he"), None)
            except:
                found_url = None
            
            if found_url and "icar.co.il" in found_url:
                full_specs = scrape_icar_specs(found_url)
                if full_specs:
                    t1, t2, t3 = st.tabs(["📊 מפרט ומידות", "🛡️ בטיחות", "💎 אבזור ונוחות"])
                    with t1:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("### מנוע וביצועים")
                            for k, v in full_specs["מנוע וביצועים"].items(): st.write(f"**{k}:** {v}")
                        with c2:
                            st.write("### מידות")
                            for k, v in full_specs["מידות"].items(): st.write(f"**{k}:** {v}")
                    with t2:
                        st.write("### מערכות בטיחות")
                        st.write(" • " + "\n • ".join(full_specs["אבזור בטיחות"]) if full_specs["אבזור בטיחות"] else "לא נמצא פירוט")
                    with t3:
                        st.write("### מולטימדיה")
                        st.info(", ".join(full_specs["מולטימדיה"]) if full_specs["מולטימדיה"] else "לא נמצא פירוט")
                        st.write("### אבזור נוחות")
                        st.write(" • " + "\n • ".join(full_specs["אבזור נוחות"]) if full_specs["אבזור נוחות"] else "לא נמצא פירוט")
                else:
                    st.error("לא הצלחנו לחלץ את המפרט מהדף שנמצא.")
            else:
                st.error("לא נמצא דף תואם ב-iCar.")
        else:
            st.error("מספר הרישוי לא נמצא במאגר הממשלתי.")

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("""
    <div class="footer">
        המידע מ-iCar ובאחריותם בלבד. | קרדיט ליואב מורד על בניית האתר.
    </div>
    """, unsafe_allow_html=True)
