import streamlit as st
import pandas as pd
import io
import google.generativeai as genai

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AI Data Cleaner Pro",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
}

/* Glow Title */
h1 {
    text-align: center;
    font-size: 3rem;
    background: linear-gradient(90deg, #00f3ff, #ff00e6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
    margin-bottom: 0;
}

/* Subtitle */
.subtitle {
    text-align: center;
    color: #00f3ff;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Cards */
.st-emotion-cache-1y4p8pa, .st-emotion-cache-12w0qpk {
    background: rgba(26, 26, 46, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid #00f3ff;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.1);
    padding: 20px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #00f3ff, #0099cc);
    color: black;
    font-weight: bold;
    border-radius: 30px;
    border: none;
    padding: 10px 30px;
    transition: all 0.5s ease;
    width: 100%;
    font-size: 1.2rem;
}

.stButton > button:hover {
    box-shadow: 0 0 25px #00f3ff;
    transform: scale(1.02);
    background: linear-gradient(90deg, #00e6ff, #00b3ff);
}

/* File uploader */
.st-emotion-cache-1h9usn1 {
    background: rgba(26, 26, 46, 0.6);
    border-radius: 15px;
    border: 1px dashed #00f3ff;
    padding: 20px;
}

/* Success message */
.stAlert {
    background: rgba(0, 243, 255, 0.15);
    border-radius: 12px;
    border-left: 4px solid #00f3ff;
}

/* Metrics */
.stMetric {
    background: rgba(26, 26, 46, 0.7);
    border-radius: 15px;
    padding: 10px;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 3rem;
    color: #555;
    font-size: 0.8rem;
}
</style>

<div class="footer">⚡ AI Data Cleaner Pro | Powered by Gemini 3 Flash</div>
""", unsafe_allow_html=True)

# ==================== TITLE ====================
st.title("🧹 AI Data Cleaning Assistant")
st.markdown('<p class="subtitle">Upload messy CSV/Excel — AI cleans it instantly</p>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    api_key = st.text_input(
        "🔑 Google Gemini API Key",
        type="password",
        help="Get from aistudio.google.com for free",
        placeholder="Paste your API key here..."
    )
    
    st.markdown("---")
    st.markdown("## 🛠️ Cleaning Options")
    
    remove_duplicates = st.checkbox("🗑️ Remove duplicate rows", value=True)
    fix_whitespace = st.checkbox("📝 Fix whitespace in text", value=True)
    fill_missing = st.checkbox("📊 Fill missing values (AI powered)", value=True)
    lowercase_text = st.checkbox("🔡 Convert text to lowercase", value=False)
    
    st.markdown("---")
    st.markdown("### 📌 How to use")
    st.markdown("""
    1. Enter your Gemini API Key
    2. Upload CSV or Excel file
    3. Choose cleaning options
    4. Click 'Start Cleaning'
    5. Download cleaned file
    """)

# ==================== MAIN CONTENT ====================
uploaded_file = st.file_uploader(
    "📂 Choose a CSV or Excel file",
    type=['csv', 'xlsx', 'xls'],
    help="Upload any messy file — AI will clean it"
)

if uploaded_file is not None:
    try:
        # Read file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File loaded! `{df.shape[0]}` rows, `{df.shape[1]}` columns")
        
        # Show preview
        with st.expander("🔍 Preview Original Data"):
            st.dataframe(df.head(10), use_container_width=True)
        
        # Cleaning button
        if st.button("✨ Start Cleaning", use_container_width=False):
            if not api_key:
                st.error("❌ Please enter your Gemini API Key in the sidebar")
            else:
                with st.spinner("🧹 AI is cleaning your data... Please wait (10-30 seconds)"):
                    original_rows = len(df)
                    cleaning_log = []
                    
                    # Configure Gemini with NEW MODEL
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    
                    # 1. Remove duplicates
                    if remove_duplicates:
                        before = len(df)
                        df = df.drop_duplicates()
                        after = len(df)
                        cleaning_log.append(f"🗑️ Removed {before - after} duplicate rows")
                    
                    # 2. Fix whitespace
                    if fix_whitespace:
                        string_cols = df.select_dtypes(include=['object']).columns
                        for col in string_cols:
                            df[col] = df[col].astype(str).str.strip()
                        cleaning_log.append(f"📝 Fixed whitespace in {len(string_cols)} text columns")
                    
                    # 3. Fill missing values with AI (Gemini 3 Flash)
                    if fill_missing:
                        missing_cols = df.columns[df.isnull().any()].tolist()
                        
                        if missing_cols:
                            for col in missing_cols:
                                if df[col].dtype == 'object':
                                    sample_values = df[col].dropna().head(3).tolist()
                                    if sample_values:
                                        prompt = f"""Column '{col}' has missing values. Based on these examples: {sample_values}
                                        What value should replace missing values? Answer with ONLY one word or number, no explanation."""
                                        
                                        try:
                                            response = model.generate_content(prompt)
                                            fill_val = response.text.strip()
                                            df[col] = df[col].fillna(fill_val)
                                            cleaning_log.append(f"🤖 AI filled '{col}' missing with: {fill_val}")
                                        except:
                                            df[col] = df[col].fillna("Missing")
                                            cleaning_log.append(f"⚠️ Filled '{col}' with: Missing")
                                else:
                                    df[col] = df[col].fillna(df[col].median() if df[col].dtype in ['int64', 'float64'] else 0)
                                    cleaning_log.append(f"📊 Filled numeric missing in '{col}' with median/0")
                        else:
                            cleaning_log.append("✅ No missing values found in any column")
                    
                    # 4. Lowercase text
                    if lowercase_text:
                        string_cols = df.select_dtypes(include=['object']).columns
                        for col in string_cols:
                            df[col] = df[col].astype(str).str.lower()
                        cleaning_log.append(f"🔡 Converted {len(string_cols)} text columns to lowercase")
                    
                    # Show results
                    st.markdown("---")
                    st.markdown("## 🎉 Cleaning Complete!")
                    
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Original Rows", original_rows)
                    with col2:
                        st.metric("Cleaned Rows", len(df))
                    with col3:
                        st.metric("Rows Removed", original_rows - len(df))
                    
                    # Cleaning log
                    with st.expander("📋 Cleaning Log"):
                        for log in cleaning_log:
                            st.write(f"• {log}")
                    
                    # Preview cleaned data
                    with st.expander("🔍 Preview Cleaned Data"):
                        st.dataframe(df.head(10), use_container_width=True)
                    
                    # Download button
                    output = io.BytesIO()
                    df.to_csv(output, index=False)
                    st.download_button(
                        label="💾 Download Cleaned CSV",
                        data=output.getvalue(),
                        file_name="cleaned_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Make sure your file is valid CSV or Excel format")

else:
    st.info("👈 Upload a CSV or Excel file to get started")
