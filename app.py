import streamlit as st
import os
import json
import time
from datetime import datetime
from groq import Groq
import PyPDF2
import docx
import io
import base64
from PIL import Image

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BAi Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 179, 237, 0.2);
    }
    .main-header h1 { 
        color: #63b3ed; 
        font-size: 2.2rem; 
        font-weight: 700; 
        margin: 0;
    }
    .main-header p { 
        color: #a0aec0; 
        margin: 0.5rem 0 0 0; 
        font-size: 1rem;
    }
    
    .agent-card {
        background: linear-gradient(135deg, #1a202c, #2d3748);
        border: 1px solid rgba(99, 179, 237, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .agent-card:hover { border-color: #63b3ed; }
    .agent-card h4 { color: #63b3ed; margin: 0 0 0.3rem 0; font-size: 1rem; }
    .agent-card p { color: #a0aec0; margin: 0; font-size: 0.85rem; }
    
    .result-box {
        background: #1a202c;
        border: 1px solid rgba(99, 179, 237, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #2d3748, #1a202c);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(99, 179, 237, 0.2);
    }
    .metric-card .value { color: #63b3ed; font-size: 1.8rem; font-weight: 700; }
    .metric-card .label { color: #718096; font-size: 0.8rem; margin-top: 0.2rem; }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .badge-blue { background: rgba(99, 179, 237, 0.15); color: #63b3ed; border: 1px solid rgba(99, 179, 237, 0.3); }
    .badge-green { background: rgba(72, 187, 120, 0.15); color: #48bb78; border: 1px solid rgba(72, 187, 120, 0.3); }
    .badge-purple { background: rgba(159, 122, 234, 0.15); color: #9f7aea; border: 1px solid rgba(159, 122, 234, 0.3); }
    
    .stButton > button {
        background: linear-gradient(135deg, #3182ce, #2b6cb0) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2b6cb0, #2c5282) !important;
        transform: translateY(-1px) !important;
    }
    
    .sidebar .stSelectbox label, .sidebar .stTextArea label { color: #a0aec0 !important; }
    
    div[data-testid="stExpander"] {
        background: #1a202c;
        border: 1px solid rgba(99, 179, 237, 0.2);
        border-radius: 8px;
    }
    
    .chat-message-user {
        background: rgba(49, 130, 206, 0.15);
        border-left: 3px solid #3182ce;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #e2e8f0;
    }
    .chat-message-ai {
        background: rgba(99, 179, 237, 0.08);
        border-left: 3px solid #63b3ed;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ─── BA System Prompt ──────────────────────────────────────────────────────────
BA_SYSTEM_PROMPT = """You are BAi — the Ultimate Business Analyst Agent, an elite AI assistant exclusively designed for Business Analysts, Product Owners, and Solution Designers.

## YOUR IDENTITY
You are not a general-purpose assistant. You are a specialized BA expert with deep mastery of:
- Business Analysis Body of Knowledge (BABOK v3)
- Agile, Scrum, SAFe, and Waterfall methodologies
- Requirements engineering (functional, non-functional, business, technical)
- Stakeholder management and elicitation techniques
- Process modeling (BPMN, UML, flowcharts, swimlane diagrams)
- Solution design and enterprise architecture patterns
- Data analysis, gap analysis, and root cause analysis
- User story writing, acceptance criteria (Gherkin/BDD)
- CBAP/CCBA certification knowledge

## YOUR CAPABILITIES
When analyzing documents or answering questions, you:
1. **Extract & Structure**: Identify business requirements, functional specs, process flows, and key decisions
2. **BA Artifact Generation**: Produce BRDs, FRDs, user stories, use cases, process maps, RACI matrices, stakeholder registers
3. **Gap Analysis**: Identify missing requirements, ambiguities, contradictions, and risk areas
4. **Recommendations**: Provide actionable, prioritized recommendations using MoSCoW, Kano, or weighted scoring
5. **Diagrams in Text**: Generate Mermaid.js-compatible diagrams for processes, data flows, and use cases

## YOUR TONE & FORMAT
- Professional, precise, and structured
- Use headers, bullet points, tables, and numbered lists
- Lead with the most critical insights
- Always include a "BA Recommendations" section
- Flag risks and assumptions explicitly
- When in doubt, ask clarifying questions like a real BA would

## DOCUMENT ANALYSIS MODE
When documents are uploaded:
1. Provide an executive summary (3-5 sentences)
2. List key stakeholders identified
3. Extract all functional and non-functional requirements
4. Identify process flows and data entities
5. Highlight gaps, risks, and open questions
6. Suggest next steps in the BA lifecycle

You are the smartest BA in the room. Be thorough, be precise, be indispensable."""

# ─── Groq Client ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_groq_client(api_key):
    return Groq(api_key=api_key)

# ─── Document Extraction ───────────────────────────────────────────────────────
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text.strip()
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_txt(file):
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        return f"Error reading TXT: {str(e)}"

def extract_text_from_image(file, client):
    try:
        image = Image.open(file)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                        },
                        {
                            "type": "text",
                            "text": "Extract ALL text from this image exactly as it appears. If it contains diagrams, tables, or process flows, describe them in detail as a Business Analyst would."
                        }
                    ]
                }
            ],
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error reading image: {str(e)}"

def extract_document_text(uploaded_file, client=None):
    file_type = uploaded_file.name.split(".")[-1].lower()
    if file_type == "pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type in ["docx", "doc"]:
        return extract_text_from_docx(uploaded_file)
    elif file_type == "txt":
        return extract_text_from_txt(uploaded_file)
    elif file_type in ["png", "jpg", "jpeg"]:
        if client:
            return extract_text_from_image(uploaded_file, client)
        else:
            return "Please enter your Groq API key to process images."
    else:
        return "Unsupported file type."

# ─── Groq API Call ─────────────────────────────────────────────────────────────
def call_groq(client, messages, model, temperature=0.7, max_tokens=4096):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content, response.usage
    except Exception as e:
        return f"Error: {str(e)}", None

# ─── Session State Init ────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "doc_context" not in st.session_state:
    st.session_state.doc_context = ""
if "doc_name" not in st.session_state:
    st.session_state.doc_name = ""
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_runs" not in st.session_state:
    st.session_state.total_runs = 0
if "saved_outputs" not in st.session_state:
    st.session_state.saved_outputs = []

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0;'>
        <div style='font-size: 2.5rem;'>🧠</div>
        <div style='color: #63b3ed; font-size: 1.3rem; font-weight: 700;'>BAi Studio</div>
        <div style='color: #718096; font-size: 0.8rem;'>Business Analysis Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    api_key = st.secrets.get("GROQ_API_KEY", "")
    st.divider()

    st.markdown("**⚡ Model**")
    model_options = {
        "llama-3.3-70b-versatile": "LLaMA 3.3 70B (Best)",
        "llama3-70b-8192": "LLaMA 3 70B",
        "mixtral-8x7b-32768": "Mixtral 8x7B",
        "gemma2-9b-it": "Gemma 2 9B (Fast)"
    }
    selected_model = st.selectbox("", options=list(model_options.keys()), format_func=lambda x: model_options[x], label_visibility="collapsed")

    st.markdown("**🌡️ Creativity**")
    temperature = st.slider("", 0.0, 1.0, 0.7, 0.05, label_visibility="collapsed")

    st.divider()

    st.markdown("**📊 Session Stats**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class='metric-card'><div class='value'>{st.session_state.total_runs}</div><div class='label'>Runs</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='metric-card'><div class='value'>{len(st.session_state.saved_outputs)}</div><div class='label'>Saved</div></div>""", unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.doc_context = ""
        st.session_state.doc_name = ""
        st.session_state.total_runs = 0
        st.session_state.saved_outputs = []
        st.rerun()

# ─── Main Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class='main-header'>
    <h1>🧠 BAi Studio</h1>
    <p>Your AI-Powered Business Analysis Command Center — Powered by Groq + LLaMA</p>
    <div style='margin-top: 1rem;'>
        <span class='badge badge-green'>⚡ Zero Latency</span>
        <span class='badge badge-blue'>🔒 100% Private</span>
        <span class='badge badge-purple'>💰 Free to Use</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 BA Chat",
    "📄 Doc Analyser",
    "📝 Artifact Generator",
    "🔍 BA Toolkit",
    "💾 Saved Outputs"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BA CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 💬 Chat with Your BA Agent")
    st.markdown("<span class='badge badge-blue'>Context-aware</span> <span class='badge badge-green'>BABOK-trained</span> <span class='badge badge-purple'>Document-ready</span>", unsafe_allow_html=True)

    if st.session_state.doc_name:
        st.info(f"📎 Document in context: **{st.session_state.doc_name}** — BAi will reference it in responses.")

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-message-user'>👤 <strong>You:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f"<div class='chat-message-ai'>🧠 <strong>BAi:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask BAi anything...",
            placeholder="e.g. Write user stories for a login feature, Explain BABOK elicitation techniques, Review this requirement...",
            height=100
        )
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submitted = st.form_submit_button("🚀 Send to BAi", use_container_width=True)
        with col2:
            save_response = st.form_submit_button("💾 Send & Save", use_container_width=True)
        with col3:
            clear_chat = st.form_submit_button("🗑️ Clear Chat", use_container_width=True)

    if clear_chat:
        st.session_state.chat_history = []
        st.rerun()

    if (submitted or save_response) and user_input.strip():
        if not api_key:
            st.error("Please enter your Groq API key in the sidebar.")
        else:
            client = get_groq_client(api_key)
            messages = [{"role": "system", "content": BA_SYSTEM_PROMPT}]
            if st.session_state.doc_context:
                messages.append({
                    "role": "system",
                    "content": f"Document uploaded by user ({st.session_state.doc_name}):\n\n{st.session_state.doc_context[:6000]}"
                })
            for msg in st.session_state.chat_history[-10:]:
                messages.append(msg)
            messages.append({"role": "user", "content": user_input})

            with st.spinner("🧠 BAi is analysing..."):
                response, usage = call_groq(client, messages, selected_model, temperature)

            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.total_runs += 1
            if usage:
                st.session_state.total_tokens += usage.total_tokens
            if save_response:
                st.session_state.saved_outputs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "Chat",
                    "input": user_input[:80] + "...",
                    "output": response
                })
                st.success("✅ Response saved!")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT ANALYSER
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📄 BA Document Analyser")
    st.markdown("Upload any business document or image and BAi will perform a full BA analysis.")

    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg"],
        help="Supported: PDF, Word (.docx), Text, Images (PNG, JPG, JPEG)"
    )

    if uploaded_file:
        client_for_image = get_groq_client(api_key) if api_key else None
        with st.spinner("📖 Reading document..."):
            doc_text = extract_document_text(uploaded_file, client_for_image)
            st.session_state.doc_context = doc_text
            st.session_state.doc_name = uploaded_file.name

        st.success(f"✅ **{uploaded_file.name}** loaded — {len(doc_text.split())} words extracted")

        with st.expander("📃 Preview Extracted Content", expanded=False):
            st.text(doc_text[:2000] + ("..." if len(doc_text) > 2000 else ""))

        st.divider()

        analysis_type = st.selectbox(
            "🎯 Select Analysis Mode",
            [
                "🔍 Full BA Analysis (Requirements + Gaps + Risks)",
                "📋 Requirements Extraction Only",
                "🔄 Process Flow Identification",
                "👥 Stakeholder Analysis",
                "⚠️ Risk & Assumption Register",
                "✅ Acceptance Criteria Generation",
                "📊 Executive Summary for BA"
            ]
        )

        custom_instruction = st.text_input(
            "➕ Additional Instructions (optional)",
            placeholder="e.g. Focus on API integration requirements, Flag GDPR compliance gaps..."
        )

        if st.button("🚀 Run BA Analysis", use_container_width=True):
            if not api_key:
                st.error("Please enter your Groq API key in the sidebar.")
            else:
                client = get_groq_client(api_key)
                prompt = f"""Perform the following analysis on the uploaded document:
{analysis_type}

{f'Additional focus: {custom_instruction}' if custom_instruction else ''}

Document content:
{doc_text[:7000]}

Provide a thorough, structured BA analysis with all relevant sections, tables, and recommendations."""

                messages = [
                    {"role": "system", "content": BA_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]

                with st.spinner("🧠 Running deep BA analysis..."):
                    result, usage = call_groq(client, messages, selected_model, temperature, max_tokens=4096)

                st.session_state.total_runs += 1
                st.markdown("---")
                st.markdown("### 📊 Analysis Results")
                st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save This Analysis"):
                        st.session_state.saved_outputs.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "type": f"Doc Analysis: {uploaded_file.name}",
                            "input": analysis_type,
                            "output": result
                        })
                        st.success("Saved!")
                with col2:
                    st.download_button(
                        "⬇️ Download as TXT",
                        data=result,
                        file_name=f"ba_analysis_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ARTIFACT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📝 BA Artifact Generator")
    st.markdown("Generate professional BA documents instantly.")

    artifact_type = st.selectbox(
        "📋 Select Artifact Type",
        [
            "User Stories with Acceptance Criteria (Gherkin)",
            "Business Requirements Document (BRD) Template",
            "Functional Requirements Specification (FRS)",
            "Use Case Document",
            "Process Flow (Mermaid Diagram)",
            "Data Flow Diagram (DFD) Description",
            "RACI Matrix",
            "Stakeholder Register",
            "Gap Analysis Report",
            "Business Case Document",
            "Change Request Form",
            "Test Case Scenarios (BA Perspective)",
            "Non-Functional Requirements (NFRs)",
            "Traceability Matrix",
            "Sprint User Stories (Agile Backlog)"
        ]
    )

    context_input = st.text_area(
        "📌 Describe Your Project/Feature",
        placeholder="e.g. An e-commerce platform for a Canadian retailer needing a loyalty points system...",
        height=150
    )

    col1, col2 = st.columns(2)
    with col1:
        domain = st.selectbox("🏢 Domain", [
            "General", "Banking & Finance", "Healthcare", "Retail & E-Commerce",
            "Government", "Insurance", "Telecom", "Manufacturing", "HR & Payroll", "ERP/SAP"
        ])
    with col2:
        methodology = st.selectbox("⚙️ Methodology", ["Agile/Scrum", "Waterfall", "SAFe", "Hybrid", "Kanban"])

    if st.button("⚡ Generate Artifact", use_container_width=True):
        if not api_key:
            st.error("Please enter your Groq API key in the sidebar.")
        elif not context_input.strip():
            st.warning("Please describe your project or feature.")
        else:
            client = get_groq_client(api_key)
            prompt = f"""Generate a professional, complete BA artifact:

Artifact Type: {artifact_type}
Domain: {domain}
Methodology: {methodology}

Project/Feature Description:
{context_input}

{'Reference the uploaded document if relevant: ' + st.session_state.doc_name if st.session_state.doc_context else ''}

Produce a complete, ready-to-use {artifact_type} that a senior BA would be proud to submit."""

            messages = [
                {"role": "system", "content": BA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]

            with st.spinner(f"✍️ Generating {artifact_type}..."):
                result, usage = call_groq(client, messages, selected_model, temperature, max_tokens=4096)

            st.session_state.total_runs += 1
            st.markdown("---")
            st.markdown(f"### 📋 {artifact_type}")
            st.markdown(result)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Artifact"):
                    st.session_state.saved_outputs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "type": artifact_type,
                        "input": context_input[:80] + "...",
                        "output": result
                    })
                    st.success("Saved!")
            with col2:
                st.download_button(
                    "⬇️ Download Artifact",
                    data=result,
                    file_name=f"{artifact_type.replace(' ', '_')[:30]}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — BA TOOLKIT
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🔍 BA Toolkit")

    toolkit_col1, toolkit_col2 = st.columns(2)

    with toolkit_col1:
        st.markdown("#### Quick BA Tools")

        tool = st.selectbox("🛠️ Select Tool", [
            "MoSCoW Prioritisation",
            "Root Cause Analysis (5 Whys)",
            "SWOT Analysis",
            "Feasibility Assessment",
            "Agile Story Point Estimation",
            "Requirement Smell Detector",
            "Stakeholder Power/Interest Grid",
            "PESTLE Analysis",
            "Kano Model Analysis",
            "Business Value Calculator"
        ])

        tool_input = st.text_area(
            "Describe what you need to analyse",
            height=120,
            placeholder="Describe your requirements, features, or situation..."
        )

        if st.button("⚡ Run Tool", use_container_width=True):
            if not api_key:
                st.error("Add your Groq API key in the sidebar.")
            elif not tool_input.strip():
                st.warning("Please enter a description.")
            else:
                client = get_groq_client(api_key)
                prompt = f"""As a senior BA, apply the {tool} framework to the following:

{tool_input}

Provide a detailed, structured output using proper {tool} format with clear sections, tables where appropriate, and actionable BA recommendations."""

                messages = [
                    {"role": "system", "content": BA_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]

                with st.spinner(f"🔍 Running {tool}..."):
                    result, usage = call_groq(client, messages, selected_model, temperature)

                st.session_state.total_runs += 1
                st.markdown("---")
                st.markdown(result)

                if st.button("💾 Save Tool Output", key="save_tool"):
                    st.session_state.saved_outputs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "type": f"Toolkit: {tool}",
                        "input": tool_input[:80],
                        "output": result
                    })

    with toolkit_col2:
        st.markdown("#### BA Knowledge Base")

        st.markdown("""
        <div class='agent-card'>
            <h4>📚 BABOK v3 Quick Reference</h4>
            <p>6 Knowledge Areas · 50+ Techniques · Best Practices</p>
        </div>
        <div class='agent-card'>
            <h4>🎯 Elicitation Techniques</h4>
            <p>Interviews · Workshops · Surveys · Observation · Prototyping</p>
        </div>
        <div class='agent-card'>
            <h4>📐 Modelling Notations</h4>
            <p>BPMN 2.0 · UML · ERD · DFD · Swimlane · Wireframes</p>
        </div>
        <div class='agent-card'>
            <h4>⚙️ Methodologies</h4>
            <p>Agile · Waterfall · SAFe · Kanban · PRINCE2 · Hybrid</p>
        </div>
        <div class='agent-card'>
            <h4>✅ CBAP Exam Prep</h4>
            <p>Ask BAi any CBAP topic in the Chat tab for guided prep</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("#### 🔥 Quick Prompts")

        quick_prompts = [
            "Write 5 user stories for a customer portal login",
            "What are the 6 BABOK knowledge areas?",
            "Create a RACI matrix for an ERP implementation",
            "Explain BDD acceptance criteria with examples",
            "What questions should a BA ask in discovery?",
            "Write NFRs for a banking mobile app"
        ]

        for qp in quick_prompts:
            if st.button(f"▶ {qp}", key=f"qp_{qp[:20]}", use_container_width=True):
                if not api_key:
                    st.error("Add your Groq API key in the sidebar.")
                else:
                    client = get_groq_client(api_key)
                    messages = [
                        {"role": "system", "content": BA_SYSTEM_PROMPT},
                        {"role": "user", "content": qp}
                    ]
                    with st.spinner("🧠 BAi is thinking..."):
                        result, usage = call_groq(client, messages, selected_model, temperature)

                    st.session_state.chat_history.append({"role": "user", "content": qp})
                    st.session_state.chat_history.append({"role": "assistant", "content": result})
                    st.session_state.total_runs += 1
                    st.info("✅ Response added to Chat tab!")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SAVED OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 💾 Saved Outputs")

    if not st.session_state.saved_outputs:
        st.markdown("""
        <div style='text-align:center; padding: 3rem; color: #718096;'>
            <div style='font-size: 3rem;'>📂</div>
            <div style='margin-top: 1rem; font-size: 1.1rem;'>No saved outputs yet.</div>
            <div style='font-size: 0.9rem; margin-top: 0.5rem;'>Use the 💾 Save buttons in other tabs to save your work here.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        all_outputs = "\n\n" + "="*60 + "\n\n".join([
            f"[{o['timestamp']}] {o['type']}\nInput: {o['input']}\n\nOutput:\n{o['output']}"
            for o in st.session_state.saved_outputs
        ])

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{len(st.session_state.saved_outputs)} saved item(s)**")
        with col2:
            st.download_button(
                "⬇️ Export All",
                data=all_outputs,
                file_name=f"bai_studio_outputs_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.divider()

        for i, output in enumerate(reversed(st.session_state.saved_outputs)):
            idx = len(st.session_state.saved_outputs) - 1 - i
            with st.expander(f"📄 [{output['timestamp']}] {output['type']}", expanded=False):
                st.markdown(f"**Input:** {output['input']}")
                st.divider()
                st.markdown(output['output'])

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "⬇️ Download",
                        data=output['output'],
                        file_name=f"bai_{output['type'].replace(' ', '_')[:25]}_{output['timestamp'].replace(':', '').replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"dl_{idx}"
                    )
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{idx}"):
                        st.session_state.saved_outputs.pop(idx)
                        st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color: #4a5568; font-size: 0.85rem; padding: 1rem 0;'>
    🧠 <strong style='color: #63b3ed;'>BAi Studio</strong> — Built exclusively for Business Analysts &nbsp;|&nbsp; 
    Powered by <strong>Groq + LLaMA</strong> &nbsp;|&nbsp; 
    100% Free · Private · Secure
</div>
""", unsafe_allow_html=True)