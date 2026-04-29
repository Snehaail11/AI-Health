import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
import tempfile
import os
from pathlib import Path
from PIL import Image
import json
from datetime import datetime

# ========== PDF TEXT EXTRACTION (FIXED) ==========
try:
    import PyPDF2
    PDF_TEXT_AVAILABLE = True
except ImportError:
    PDF_TEXT_AVAILABLE = False
    st.warning("Installing PyPDF2 for PDF text extraction...")
    os.system("pip install PyPDF2")
    import PyPDF2

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# Configure Tesseract path
if TESSERACT_AVAILABLE:
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

# Page config
st.set_page_config(
    page_title="AI Health Report Analyzer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .insight-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .risk-moderate {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .risk-low {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .disclaimer {
        background-color: #ffebee;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 2rem;
        text-align: center;
        border: 1px solid #f44336;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🏥 AI Health Report Analyzer</h1><p>Upload any health report - AI extracts text and provides personalized insights</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📊 About")
    st.markdown("""
    This AI-powered tool analyzes your health reports and provides:
    
    | Category | Description |
    |----------|-------------|
    | 📋 **What It Means** | Plain English explanation |
    | ❓ **Why Happened** | Potential causes |
    | 🩺 **How to Care** | Immediate actions |
    | 📅 **Next Steps** | Follow-up recommendations |
    | 🥗 **Diet** | Specific food advice |
    | 🏃 **Exercises** | Safe activities |
    """)
    
    st.markdown("---")
    st.markdown("### 📁 Supported Formats")
    st.markdown("""
    - 🖼️ **Images**: JPG, PNG, JPEG
    - 📄 **PDFs** (text + scanned)
    - 📝 **Text files**: TXT
    """)
    
    st.markdown("---")
    st.markdown("### 🔬 AI Capabilities")
    st.markdown("""
    - Optical Character Recognition (OCR)
    - Medical Entity Extraction
    - Disease Risk Prediction
    - Health Score Calculation
    - Personalized Recommendations
    """)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# ========== IMPROVED PDF TEXT EXTRACTION ==========
def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using multiple methods"""
    all_text = ""
    
    # METHOD 1: PyPDF2 (for text-based PDFs - FASTEST)
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    all_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        if all_text.strip():
            return all_text.strip()
    except Exception as e:
        st.warning(f"PyPDF2 extraction failed: {e}")
    
    # METHOD 2: Try pdfplumber if available (better extraction)
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    all_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        if all_text.strip():
            return all_text.strip()
    except ImportError:
        pass
    except Exception as e:
        st.warning(f"pdfplumber extraction failed: {e}")
    
    # METHOD 3: OCR for scanned PDFs (if no text found and OCR available)
    if not all_text.strip() and PDF2IMAGE_AVAILABLE and TESSERACT_AVAILABLE:
        st.info("No text found in PDF. Trying OCR on scanned pages...")
        try:
            # Try to find poppler
            poppler_paths = [
                r'C:\poppler\bin',
                r'C:\poppler\Library\bin',
            ]
            poppler_found = None
            for pp in poppler_paths:
                if os.path.exists(pp):
                    poppler_found = pp
                    break
            
            if poppler_found:
                images = convert_from_path(pdf_path, poppler_path=poppler_found, first_page=1, last_page=10)
            else:
                images = convert_from_path(pdf_path, first_page=1, last_page=10)
            
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                if page_text.strip():
                    all_text += f"\n--- Page {i+1} (OCR) ---\n{page_text}\n"
            
            return all_text.strip()
        except Exception as e:
            return f"PDF OCR Error: {str(e)}. Install poppler from: https://github.com/oschwartz10612/poppler-windows/releases/"
    
    return all_text if all_text.strip() else "No text could be extracted from this PDF."

def extract_text_from_image(image_path):
    """Extract text from image using Tesseract OCR"""
    if not TESSERACT_AVAILABLE:
        return "OCR not available. Please install pytesseract."
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"

def extract_text_from_txt(txt_path):
    """Read text from TXT file"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_health_report(text):
    """Comprehensive health report analysis"""
    
    results = {
        "what_it_means": [],
        "why_happened": [],
        "how_to_care": [],
        "next_steps": [],
        "diet": [],
        "exercises": [],
        "health_score": 100,
        "risk_factors": [],
        "all_findings": []
    }
    
    text_lower = text.lower()
    
    # ========== TSH / THYROID (From your PDF) ==========
    # Your PDF has: "Thyroid Stimulating Hormone - 4.200 ulU/ml"
    tsh_patterns = [
        r'thyroid stimulating hormone[\s\-:]*(\d+(?:\.\d+)?)',
        r'tsh[\s\-:]*(\d+(?:\.\d+)?)',
        r'tsh[^0-9]*(\d+(?:\.\d+)?)',
        r'thyroid[^0-9]*(\d+(?:\.\d+)?)',
    ]
    
    tsh_value = None
    for pattern in tsh_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            tsh_value = float(match.group(1))
            results["all_findings"].append(f"TSH: {tsh_value} uIU/mL")
            break
    
    if tsh_value:
        # Normal range: 0.55-4.78 (from your report)
        if tsh_value > 4.78:
            results["what_it_means"].append(f"🔴 **High TSH**: {tsh_value} uIU/mL (Normal: 0.55-4.78)")
            results["what_it_means"].append("This indicates **hypothyroidism** - your thyroid gland is underactive, producing less thyroid hormone than your body needs.")
            
            results["why_happened"].append("• Hashimoto's thyroiditis (autoimmune condition - most common cause)")
            results["why_happened"].append("• Iodine deficiency")
            results["why_happened"].append("• Previous thyroid surgery or radiation")
            results["why_happened"].append("• Certain medications (lithium, amiodarone)")
            
            results["how_to_care"].append("• Take levothyroxine medication exactly as prescribed")
            results["how_to_care"].append("• Take thyroid medication on empty stomach, 30-60 minutes before breakfast")
            results["how_to_care"].append("• Never skip doses - consistency is essential")
            results["how_to_care"].append("• Avoid taking with calcium or iron supplements (wait 4 hours)")
            
            results["next_steps"].append("• Repeat TSH test in 6-8 weeks after starting/ adjusting medication")
            results["next_steps"].append("• Get Free T4 level checked")
            results["next_steps"].append("• Anti-thyroid peroxidase (TPO) antibody test")
            results["next_steps"].append("• Annual thyroid function monitoring once stable")
            
            results["diet"].append("✅ **Thyroid-healthy diet:**")
            results["diet"].append("• Selenium-rich: Brazil nuts (2-3 daily), tuna, sardines, eggs")
            results["diet"].append("• Zinc-rich: Shellfish, beef, chicken, chickpeas, pumpkin seeds")
            results["diet"].append("• Iodine: Use iodized salt in moderation")
            results["diet"].append("• Take thyroid medication correctly - this is most important")
            results["diet"].append("⚠️ **Avoid:** Taking thyroid medication with coffee, calcium, or iron supplements")
            
            results["exercises"].append("🏃 **Start slowly if experiencing fatigue:**")
            results["exercises"].append("• Light walking: 10-15 minutes daily to start")
            results["exercises"].append("• Gentle yoga (focus on thyroid-stimulating poses: shoulder stand, fish pose)")
            results["exercises"].append("• Gradually increase intensity as energy levels improve")
            results["exercises"].append("• Listen to your body - rest when needed")
            
            results["health_score"] -= 25
            results["risk_factors"].append("Hypothyroidism")
            
        elif tsh_value > 4.0:
            results["what_it_means"].append(f"🟡 **Borderline High TSH**: {tsh_value} uIU/mL (Normal: 0.55-4.78)")
            results["what_it_means"].append("This is in the **high-normal range** - monitor closely as it may indicate early hypothyroidism.")
            
            results["why_happened"].append("• Early Hashimoto's thyroiditis")
            results["why_happened"].append("• May be temporary due to illness or stress")
            results["why_happened"].append("• Recent medication changes")
            
            results["how_to_care"].append("• Discuss with your doctor about repeating the test in 3 months")
            results["how_to_care"].append("• Consider lifestyle changes to support thyroid health")
            results["how_to_care"].append("• Track symptoms like fatigue, weight gain, cold sensitivity")
            
            results["next_steps"].append("• Repeat TSH in 2-3 months")
            results["next_steps"].append("• Check thyroid antibodies (TPO, TgAb)")
            results["next_steps"].append("• Consider Free T4 test")
            
            results["diet"].append("✅ **Support thyroid health:**")
            results["diet"].append("• Brazil nuts (selenium) - 2-3 daily")
            results["diet"].append("• Zinc-rich foods (shellfish, pumpkin seeds)")
            results["diet"].append("• Adequate protein intake")
            
            results["exercises"].append("🏃 **Maintain regular activity:**")
            results["exercises"].append("• 30 minutes moderate exercise, 5 days/week")
            results["exercises"].append("• Include both cardio and strength training")
            
            results["health_score"] -= 10
            results["risk_factors"].append("Borderline TSH - Monitor Thyroid")
            
        elif tsh_value < 0.55:
            results["what_it_means"].append(f"🔴 **Low TSH**: {tsh_value} uIU/mL (Normal: 0.55-4.78)")
            results["what_it_means"].append("This indicates **hyperthyroidism** - your thyroid is overactive.")
            
            results["why_happened"].append("• Graves' disease (autoimmune)")
            results["why_happened"].append("• Thyroid nodules")
            results["why_happened"].append("• Thyroiditis (inflammation)")
            results["why_happened"].append("• Excessive thyroid medication")
            
            results["how_to_care"].append("• Take anti-thyroid medications as prescribed")
            results["how_to_care"].append("• Avoid caffeine and stimulants")
            results["how_to_care"].append("• Practice stress management techniques")
            
            results["next_steps"].append("• Free T3 and Free T4 tests")
            results["next_steps"].append("• Thyroid uptake scan")
            results["next_steps"].append("• TSH receptor antibody test")
            
            results["diet"].append("✅ **Hyperthyroidism diet:**")
            results["diet"].append("• Calcium-rich foods (for bone health)")
            results["diet"].append("• Low-iodine foods")
            
            results["exercises"].append("🏃 **Gentle exercises only:**")
            results["exercises"].append("• Walking, gentle yoga")
            results["exercises"].append("• Avoid high-intensity workouts")
            
            results["health_score"] -= 20
            results["risk_factors"].append("Hyperthyroidism")
        else:
            results["what_it_means"].append(f"✅ **Normal TSH**: {tsh_value} uIU/mL (Normal: 0.55-4.78)")
    
    # ========== CHOLESTEROL ANALYSIS ==========
    cholesterol_patterns = [
        r'cholesterol[\s:]*(\d+)',
        r'total cholesterol[\s:]*(\d+)',
    ]
    
    for pattern in cholesterol_patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = int(match.group(1))
            results["all_findings"].append(f"Cholesterol: {value} mg/dL")
            
            if value >= 240:
                results["what_it_means"].append(f"🔴 **Very High Cholesterol**: {value} mg/dL (Normal: <200)")
                results["why_happened"].append("• Diet high in saturated fats\n• Lack of physical activity\n• Genetics")
                results["how_to_care"].append("• Take statin medications as prescribed\n• Reduce saturated fat intake\n• Exercise regularly")
                results["next_steps"].append("• Repeat lipid panel in 3 months\n• Cardiac risk assessment")
                results["diet"].append("✅ **EAT MORE:** Oats, beans, nuts, olive oil, fatty fish\n❌ **AVOID:** Red meat, fried foods, full-fat dairy")
                results["exercises"].append("🏃 30 min brisk walking, 5 days/week")
                results["health_score"] -= 25
                results["risk_factors"].append("High Cholesterol")
                
            elif value >= 200:
                results["what_it_means"].append(f"🟡 **Borderline High Cholesterol**: {value} mg/dL")
                results["why_happened"].append("• Dietary choices\n• Sedentary lifestyle")
                results["how_to_care"].append("• Start lifestyle changes\n• Reduce saturated fats")
                results["next_steps"].append("• Repeat test in 3-6 months")
                results["diet"].append("✅ Increase fiber: Oats, beans, fruits, vegetables\n❌ Reduce: Saturated fats")
                results["exercises"].append("🏃 30 min walking daily")
                results["health_score"] -= 10
                results["risk_factors"].append("Borderline High Cholesterol")
            break
    
    # ========== BLOOD PRESSURE ANALYSIS ==========
    bp_patterns = [
        r'blood pressure[\s:]*(\d+)/(\d+)',
        r'bp[\s:]*(\d+)/(\d+)',
    ]
    
    for pattern in bp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            systolic = int(match.group(1))
            diastolic = int(match.group(2))
            results["all_findings"].append(f"Blood Pressure: {systolic}/{diastolic} mmHg")
            
            if systolic >= 180 or diastolic >= 120:
                results["what_it_means"].append(f"🔴 **Hypertensive Crisis**: {systolic}/{diastolic} mmHg - SEEK IMMEDIATE CARE")
                results["why_happened"].append("• Uncontrolled hypertension\n• Medical emergency")
                results["how_to_care"].append("⚠️ **SEEK IMMEDIATE MEDICAL CARE**")
                results["next_steps"].append("• Emergency evaluation")
                results["health_score"] -= 40
                results["risk_factors"].append("Hypertensive Crisis")
                
            elif systolic >= 140 or diastolic >= 90:
                results["what_it_means"].append(f"🔴 **High BP (Stage 2)**: {systolic}/{diastolic} mmHg")
                results["why_happened"].append("• High sodium intake\n• Lack of exercise\n• Stress")
                results["how_to_care"].append("• Take BP medications\n• Reduce salt immediately\n• Monitor BP daily")
                results["next_steps"].append("• Follow up within 1 month\n• Start DASH diet")
                results["diet"].append("🥬 **DASH Diet:** Low sodium (<1500mg/day), potassium-rich foods")
                results["exercises"].append("🏃 30 minutes walking, swimming, or cycling daily")
                results["health_score"] -= 20
                results["risk_factors"].append("Stage 2 Hypertension")
                
            elif systolic >= 130 or diastolic >= 80:
                results["what_it_means"].append(f"🟡 **Elevated BP (Stage 1)**: {systolic}/{diastolic} mmHg")
                results["why_happened"].append("• Dietary factors\n• Stress\n• Limited exercise")
                results["how_to_care"].append("• Start lifestyle modifications\n• Reduce sodium")
                results["next_steps"].append("• Recheck in 3-6 months\n• DASH diet")
                results["diet"].append("🥬 Reduce sodium to <2300mg/day, increase fruits/vegetables")
                results["exercises"].append("🏃 30 minutes moderate exercise, 5 days/week")
                results["health_score"] -= 10
                results["risk_factors"].append("Pre-hypertension")
            break
    
    # ========== GLUCOSE/DIABETES ==========
    glucose_match = re.search(r'glucose[\s:]*(\d+)', text_lower)
    if glucose_match:
        value = int(glucose_match.group(1))
        results["all_findings"].append(f"Glucose: {value} mg/dL")
        
        if value >= 200:
            results["what_it_means"].append(f"🔴 **Very High Blood Sugar**: {value} mg/dL - Possible diabetes")
            results["why_happened"].append("• Diabetes\n• Missed medication")
            results["how_to_care"].append("• Take diabetes medications\n• Monitor blood sugar")
            results["next_steps"].append("• HbA1c test\n• Consult endocrinologist")
            results["diet"].append("🍽️ Low glycemic foods, avoid sugar")
            results["exercises"].append("🏃 Exercise after meals")
            results["health_score"] -= 30
            results["risk_factors"].append("Diabetes")
            
        elif value >= 126:
            results["what_it_means"].append(f"🔴 **High Blood Sugar**: {value} mg/dL - Diabetes range")
            results["why_happened"].append("• Insulin resistance\n• Diet high in sugar")
            results["how_to_care"].append("• Start monitoring blood glucose\n• Reduce sugar intake")
            results["next_steps"].append("• HbA1c test")
            results["diet"].append("✅ Low glycemic foods\n❌ Avoid sugar, white bread, soda")
            results["exercises"].append("🏃 Exercise after meals")
            results["health_score"] -= 25
            results["risk_factors"].append("High Blood Sugar")
            
        elif value >= 100:
            results["what_it_means"].append(f"🟡 **Prediabetes**: {value} mg/dL")
            results["why_happened"].append("• Insulin resistance developing")
            results["how_to_care"].append("• Lose 5-7% body weight\n• Increase exercise")
            results["next_steps"].append("• Repeat glucose in 3 months")
            results["diet"].append("✅ Reduce added sugars, increase fiber")
            results["exercises"].append("🏃 150 minutes exercise weekly")
            results["health_score"] -= 10
            results["risk_factors"].append("Prediabetes")
    
    # ========== HEMOGLOBIN/ANEMIA ==========
    hb_match = re.search(r'hemoglobin[\s:]*(\d+(?:\.\d+)?)', text_lower)
    if hb_match:
        value = float(hb_match.group(1))
        results["all_findings"].append(f"Hemoglobin: {value} g/dL")
        
        if value < 11:
            results["what_it_means"].append(f"🔴 **Severe Anemia**: {value} g/dL (Normal: 12-16)")
            results["why_happened"].append("• Severe iron deficiency\n• Blood loss")
            results["how_to_care"].append("• Iron supplements as prescribed")
            results["next_steps"].append("• Complete blood count\n• Iron studies")
            results["diet"].append("🥩 Iron-rich: Red meat, spinach, lentils")
            results["exercises"].append("🩹 Rest until levels improve")
            results["health_score"] -= 25
            results["risk_factors"].append("Severe Anemia")
            
        elif value < 12:
            results["what_it_means"].append(f"🟡 **Mild Anemia**: {value} g/dL")
            results["why_happened"].append("• Mild iron deficiency")
            results["how_to_care"].append("• Increase iron-rich foods")
            results["next_steps"].append("• Repeat CBC in 3 months")
            results["diet"].append("✅ Iron-rich foods + Vitamin C for absorption")
            results["exercises"].append("🏃 Normal exercise OK")
            results["health_score"] -= 10
            results["risk_factors"].append("Mild Anemia")
    
    # ========== DEFAULT (No Issues Found) ==========
    if not results["what_it_means"]:
        results["what_it_means"].append("✅ **No Significant Abnormalities Detected**")
        results["what_it_means"].append("Based on the available data, your health metrics appear within normal ranges.")
        
        results["why_happened"].append("• Your healthy lifestyle choices are working well")
        results["why_happened"].append("• Regular check-ups help maintain good health")
        
        results["how_to_care"].append("• Continue your healthy habits")
        results["how_to_care"].append("• Keep regular check-ups")
        
        results["next_steps"].append("• Schedule next check-up in 6-12 months")
        results["next_steps"].append("• Maintain a health diary")
        
        results["diet"].append("🥗 **Balanced Diet:** Vegetables, fruits, whole grains, lean proteins, healthy fats")
        
        results["exercises"].append("🏃 **Stay Active:** 150 minutes moderate exercise weekly")
    
    # Normalize health score
    results["health_score"] = max(0, min(100, results["health_score"]))
    
    # Remove duplicates
    for key in results:
        if isinstance(results[key], list):
            results[key] = list(dict.fromkeys(results[key]))
    
    return results

def create_health_gauge(score):
    """Create health gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": "Overall Health Score", "font": {"size": 24}},
        delta={"reference": 80},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#2a5298"},
            "steps": [
                {"range": [0, 50], "color": "#ffebee"},
                {"range": [50, 70], "color": "#fff3e0"},
                {"range": [70, 85], "color": "#e8f5e9"},
                {"range": [85, 100], "color": "#c8e6c9"}
            ]
        }
    ))
    fig.update_layout(height=300)
    return fig

# ========== MAIN UI ==========
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "📁 Upload Your Health Report",
        type=["jpg", "jpeg", "png", "pdf", "txt"],
        help="Upload any medical report, lab result, or health document"
    )

with col2:
    st.markdown("### 📋 Quick Tips")
    st.markdown("""
    - **PDFs with text** are extracted directly
    - **Scanned PDFs** use OCR
    - You can also paste text below
    """)

# Manual text input
with st.expander("✏️ Or paste health report text directly"):
    manual_text = st.text_area(
        "Paste your health report text here:",
        height=150,
        placeholder="Example:\n\nThyroid Stimulating Hormone - 4.200 ulU/ml\nCholesterol: 220 mg/dL\nBlood Pressure: 135/85 mmHg"
    )

# Process file
extracted_text = ""

if uploaded_file:
    file_ext = Path(uploaded_file.name).suffix.lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    with st.spinner(f"📄 Processing {uploaded_file.name}..."):
        if file_ext == '.pdf':
            extracted_text = extract_text_from_pdf(tmp_path)
            if extracted_text and "Error" not in extracted_text:
                st.success(f"✅ Extracted text from PDF: {uploaded_file.name}")
            else:
                st.error(f"PDF extraction issue. Please try pasting the text manually.")
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            extracted_text = extract_text_from_image(tmp_path)
            st.success(f"✅ Extracted text from image: {uploaded_file.name}")
        elif file_ext == '.txt':
            extracted_text = extract_text_from_txt(tmp_path)
            st.success(f"✅ Loaded text from: {uploaded_file.name}")
    
    os.unlink(tmp_path)
    
    if extracted_text:
        with st.expander("📄 View Extracted Text"):
            st.text(extracted_text[:2000] + ("..." if len(extracted_text) > 2000 else ""))

elif manual_text:
    extracted_text = manual_text
    with st.expander("📄 View Text"):
        st.text(extracted_text[:2000])

# Analyze button
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    analyze_clicked = st.button("🚀 ANALYZE HEALTH REPORT", type="primary", use_container_width=True)

if analyze_clicked and extracted_text:
    with st.spinner("🧠 AI is analyzing your health report..."):
        results = analyze_health_report(extracted_text)
    
    st.session_state.analysis_results = results
    
    # Display results
    st.markdown("---")
    
    # Health score gauge
    st.markdown("## 📊 Health Assessment")
    fig = create_health_gauge(results["health_score"])
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk factors alert
    if results["risk_factors"]:
        st.warning(f"⚠️ **Risk Factors Identified:** {', '.join(results['risk_factors'])}")
    else:
        st.success("✅ **No significant risk factors detected**")
    
    # Detailed tabs
    st.markdown("## 📋 Detailed Analysis")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 What It Means", "❓ Why Happened", "🩺 How to Care",
        "📅 Next Steps", "🥗 Diet Plan", "🏃 Exercise Plan"
    ])
    
    with tab1:
        for item in results["what_it_means"]:
            if item.startswith(("🔴", "🟡", "✅")):
                st.markdown(f"### {item}")
            else:
                st.markdown(f"• {item}")
    
    with tab2:
        if results["why_happened"]:
            for item in results["why_happened"]:
                st.markdown(f"• {item}")
        else:
            st.info("Consult your healthcare provider for personalized information")
    
    with tab3:
        if results["how_to_care"]:
            for item in results["how_to_care"]:
                if "⚠️" in item:
                    st.error(item)
                else:
                    st.markdown(f"• {item}")
        else:
            st.info("Continue regular check-ups and maintain healthy habits")
    
    with tab4:
        if results["next_steps"]:
            for item in results["next_steps"]:
                st.markdown(f"• {item}")
        else:
            st.info("Schedule regular follow-up with your healthcare provider")
    
    with tab5:
        if results["diet"]:
            for item in results["diet"]:
                st.markdown(item)
        else:
            st.info("🥗 Follow a balanced diet with fruits, vegetables, and whole grains")
    
    with tab6:
        if results["exercises"]:
            for item in results["exercises"]:
                st.markdown(item)
        else:
            st.info("🏃 Aim for 150 minutes of moderate exercise weekly")
    
    # All findings summary
    if results["all_findings"]:
        with st.expander("🔬 All Detected Medical Findings"):
            for finding in results["all_findings"]:
                st.markdown(f"- {finding}")

elif analyze_clicked and not extracted_text:
    st.error("❌ Please upload a file or paste text before analyzing.")

# Disclaimer
st.markdown("""
<div class="disclaimer">
    <strong>⚠️ IMPORTANT MEDICAL DISCLAIMER</strong><br><br>
    This AI tool is for <strong>informational and educational purposes only</strong>.<br>
    It is NOT a substitute for professional medical advice, diagnosis, or treatment.<br>
    Always seek the advice of your physician or other qualified health provider.<br>
    <br>
    <strong>For medical emergencies, call emergency services immediately.</strong>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; color: gray; padding: 1rem; margin-top: 1rem;">
    <p>🏥 AI Health Report Analyzer | Powered by PyPDF2 + Tesseract OCR | Version 3.0</p>
</div>
""", unsafe_allow_html=True)