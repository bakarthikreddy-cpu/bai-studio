        st.markdown(f"<div class='metric-card'><div class='metric-value'>{st.session_state.run_count}</div><div class='metric-label'>Runs</div></div>", unsafe_allow_html=True)import streamlit as st
from groq import Groq
from datetime import datetime
import fitz
from docx import Document
from pptx import Presentation
import os
import json
import csv
import io as io_module
import base64
import openpyxl

st.set_page_config(page_title="BAi Studio", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main,.stApp{background:#0d1117}
    .block-container{padding:2rem 3rem}
    .hero-box{background:linear-gradient(135deg,#0d1117,#0f1e3d,#1a56db22);border-radius:20px;padding:3rem;margin-bottom:2rem;border:1px solid #1a56db44}
    .hero-logo{font-size:3rem;font-weight:900;background:linear-gradient(135deg,#1a56db,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0}
    .hero-tagline{color:#8b9ab5;font-size:1.1rem;margin-top:0.5rem}
    .badge{display:inline-block;background:#1a56db22;color:#06b6d4;border-radius:20px;padding:4px 14px;font-size:0.75rem;font-weight:600;margin-right:8px;margin-top:8px;border:1px solid #1a56db44}
    .result-box{background:#0f1e3d;border-left:4px solid #06b6d4;border-radius:0 12px 12px 0;padding:1.5rem 2rem;color:#e2e8f0;line-height:1.9}
    .metric-card{background:#0f1e3d;border-radius:12px;padding:1rem;border:1px solid #1a56db33;text-align:center}
    .metric-value{font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#1a56db,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    .metric-label{font-size:0.72rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;font-weight:600}
    .stButton>button{background:linear-gradient(135deg,#1a56db,#06b6d4);color:white;border:none;border-radius:10px;padding:0.75rem 2rem;font-size:1rem;font-weight:700;width:100%}
    .stTextArea>div>div>textarea{background:#0f1e3d;border-color:#1a56db33;color:#e2e8f0;border-radius:10px}
    div[data-testid="stSidebar"]{background:#080d14;border-right:1px solid #1a56db22}
    .sim-tag{display:inline-block;background:#0f1e3d;color:#06b6d4;border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:600;margin-right:6px;border:1px solid #1a56db33}
    .file-preview{background:#0f1e3d;border-radius:10px;padding:0.8rem 1.2rem;border:1px solid #1a56db33;margin-bottom:0.5rem;font-size:0.85rem;color:#8b9ab5}
    .footer-box{background:#080d14;border-radius:12px;padding:1.2rem 2rem;border:1px solid #1a56db22;text-align:center;margin-top:3rem;color:#4a6080;font-size:0.82rem}
    .footer-box a{color:#06b6d4;text-decoration:none;font-weight:600}
    .search-result{background:#0f1e3d;border-left:4px solid #1a56db;border-radius:0 10px 10px 0;padding:1rem 1.5rem;margin-bottom:0.5rem;font-size:0.85rem;color:#8b9ab5}
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "run_count" not in st.session_state:
    st.session_state.run_count = 0

def extract_pdf(file):
    text = ""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text.strip()

def extract_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_pptx(file):
    prs = Presentation(file)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text.strip()

def extract_image(file):
    try:
        groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
        client = Groq(api_key=groq_key)
        image_data = base64.b64encode(file.read()).decode("utf-8")
        file_name = file.name.lower()
        media_type = "image/png" if file_name.endswith(".png") else "image/jpeg"
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Extract all text and describe all content from this image in detail."},
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}}
            ]}],
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Image analysis unavailable: {str(e)}"

def extract_json(file):
    try:
        data = json.load(file)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error reading JSON: {str(e)}"

def extract_excel(file):
    try:
        wb = openpyxl.load_workbook(file)
        text = ""
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            text += f"\n--- Sheet: {sheet} ---\n"
            for row in ws.iter_rows(values_only=True):
                row_text = "\t".join([str(c) if c is not None else "" for c in row])
                if row_text.strip():
                    text += row_text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading Excel: {str(e)}"

def extract_csv(file):
    try:
        content = file.read().decode("utf-8")
        reader = csv.reader(io_module.StringIO(content))
        rows = ["\t".join(row) for row in reader]
        return "\n".join(rows)
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

def extract_text_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_pdf(uploaded_file)
    elif name.endswith((".docx", ".doc")):
        return extract_docx(uploaded_file)
    elif name.endswith(".pptx"):
        return extract_pptx(uploaded_file)
    elif name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        return extract_image(uploaded_file)
    elif name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    elif name.endswith(".json"):
        return extract_json(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return extract_excel(uploaded_file)
    elif name.endswith(".csv"):
        return extract_csv(uploaded_file)
    return None

def universal_uploader(key):
    uploaded = st.file_uploader(
        "📎 Upload documents for context (optional)",
        type=["pdf","docx","doc","pptx","png","jpg","jpeg","bmp","tiff","txt","json","xlsx","xls","csv"],
        accept_multiple_files=True,
        key=f"uploader_{key}"
    )
    context = ""
    if uploaded:
        st.markdown("**📂 Files loaded:**")
        for f in uploaded:
            size_kb = round(f.size / 1024, 1)
            st.markdown(f"<div class='file-preview'>📄 {f.name} — {size_kb} KB</div>", unsafe_allow_html=True)
            extracted = extract_text_from_file(f)
            if extracted:
                context += f"\n\n--- {f.name} ---\n{extracted[:2000]}"
    return context

def web_search(query):
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"- {r['title']}: {r['body']}")
        return "\n".join(results)
    except Exception as e:
        return f"Search unavailable: {str(e)}"

def run_crew(scenario, role, num_agents, model, temperature=0.7):
    groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    model_map = {
        "groq/llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
        "groq/llama-3.1-8b-instant": "llama-3.1-8b-instant",
        "groq/gemma2-9b-it": "gemma2-9b-it",
        "groq/compound-beta": "compound-beta"
    }
    groq_model = model_map.get(model, "llama-3.3-70b-versatile")
    personas = [
        ("Senior Business Analyst", "You are BAi the Ultimate Business Analyst Agent. You are a CBAP-certified Senior BA with 15 years experience in BABOK v3, Agile, SAFe, Waterfall, SAP, Salesforce and Kronos WFM. Always structure your output with: Executive Summary, Key Findings, Recommendations, and Next Steps. Be thorough, precise and indispensable."),
        ("Stakeholder Advocate", "You represent all stakeholder groups. Challenge assumptions and identify gaps, conflicts and missing requirements from a stakeholder perspective. Always highlight risks and open questions."),
        ("Solution Designer", "You synthesize BA findings into clear actionable solution recommendations. Focus on feasibility, business value and implementation approach. Provide a prioritized action plan.")
    ]
    client = Groq(api_key=groq_key)
    combined_result = ""
    for i in range(num_agents):
        agent_role, backstory = personas[i]
        messages = [
            {"role": "system", "content": f"You are a {agent_role}. {backstory}"},
            {"role": "user", "content": f"Analyze this scenario: {scenario}\n\nProvide a structured analysis with: Executive Summary, Key Findings, Recommendations, and Next Steps."}
        ]
        try:
            response = client.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=2048
            )
            agent_output = response.choices[0].message.content
            if num_agents > 1:
                combined_result += f"\n\n---\n### Agent: {agent_role}\n{agent_output}"
            else:
                combined_result = agent_output
        except Exception as e:
            combined_result += f"\n\nError from {agent_role}: {str(e)}"
    return combined_result

with st.sidebar:
    st.markdown("<div style='font-size:1.4rem;font-weight:900;background:linear-gradient(135deg,#1a56db,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>BAi Studio</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#4a6080;font-size:0.75rem;margin-bottom:1rem'>Business Analysis Intelligence</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='color:#8b9ab5;font-size:0.8rem;font-weight:600;margin-bottom:0.4rem'>AI MODEL</div>", unsafe_allow_html=True)
    model_choice = st.selectbox("Model", ["groq/llama-3.3-70b-versatile","groq/llama-3.1-8b-instant","groq/gemma2-9b-it","groq/compound-beta"], label_visibility="collapsed")
    st.markdown("<div style='color:#8b9ab5;font-size:0.8rem;font-weight:600;margin-bottom:0.4rem;margin-top:1rem'>AGENTS</div>", unsafe_allow_html=True)
    num_agents = st.slider("Agents", 1, 3, 1, label_visibility="collapsed")
    agent_names = ["Senior BA only","Senior BA + Stakeholder Advocate","Full Crew (BA + Advocate + Designer)"]
    st.markdown(f"<div style='color:#06b6d4;font-size:0.75rem'>Active: {agent_names[num_agents-1]}</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#8b9ab5;font-size:0.8rem;font-weight:600;margin-bottom:0.4rem;margin-top:1rem'>DEPTH</div>", unsafe_allow_html=True)
    depth = st.select_slider("Depth", options=["Quick","Standard","Deep"], value="Standard", label_visibility="collapsed")
    st.markdown("<div style='color:#8b9ab5;font-size:0.8rem;font-weight:600;margin-bottom:0.4rem;margin-top:1rem'>CREATIVITY</div>", unsafe_allow_html=True)
    temperature = st.slider("Temperature", 0.1, 1.0, 0.7, 0.1, label_visibility="collapsed")
    st.markdown("<div style='color:#8b9ab5;font-size:0.8rem;font-weight:600;margin-bottom:0.4rem;margin-top:1rem'>WEB SEARCH</div>", unsafe_allow_html=True)
    use_search = st.toggle("Search web before analysis", value=False)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='metric-card'
><div class='metric-value'>{st.session_state.run_count}</div><div class='metric-label'>Runs</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(st.session_state.history)}</div><div class='metric-label'>Saved</div></div>", unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown("---")
        for item in reversed(st.session_state.history[-5:]):
            st.markdown(f"<div style='background:#0d1117;border-radius:8px;padding:0.6rem;margin-bottom:0.4rem;border:1px solid #1a56db22;font-size:0.8rem;color:#8b9ab5'>{item['type']}<br><span style='color:#4a6080;font-size:0.72rem'>{item['time']}</span></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<a href='https://www.linkedin.com/in/karthik-reddy-t-666334232/' target='_blank' style='color:#06b6d4;text-decoration:none;font-size:0.82rem;font-weight:600'>Karthik Reddy T - LinkedIn</a>", unsafe_allow_html=True)

st.markdown("""
<div class='hero-box'>
    <div class='hero-logo'>BAi Studio</div>
    <div class='hero-tagline'>Your AI-Powered Business Analysis Workspace</div>
    <br>
    <span class='badge'>BABOK Aligned</span>
    <span class='badge'>CBAP Ready</span>
    <span class='badge'>Document Analysis</span>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Requirements Analysis", "Document Analyzer", "BA Toolkit", "Session History"])

with tab1:
    st.markdown("#### Requirements & Business Analysis")
    st.markdown("<div style='color:#8b9ab5;font-size:0.9rem;margin-bottom:1rem'>Describe your BA scenario, problem statement, or requirements challenge.</div>", unsafe_allow_html=True)
    babok_area = st.selectbox("BABOK Knowledge Area", [
        "Business Analysis Planning & Monitoring",
        "Elicitation & Collaboration",
        "Requirements Life Cycle Management",
        "Strategy Analysis",
        "Requirements Analysis & Design Definition",
        "Solution Evaluation"
    ])
    scenario = st.text_area("Scenario", placeholder="E.g. A company wants to implement a new CRM system. Identify stakeholders, elicit requirements, and define success criteria.", height=140, label_visibility="collapsed")
    doc_context_tab1 = universal_uploader("tab1")
    output_format = st.selectbox("Output Format", ["Full Structured Report", "Executive Summary Only", "Bullet Points", "BA Deliverable Format"])
    if st.button("Run BA Analysis", type="primary", key="req_run"):
        if scenario.strip():
            final_scenario = f"BABOK Area: {babok_area}\nOutput Format: {output_format}\nScenario: {scenario}"
            if doc_context_tab1:
                final_scenario += f"\n\nUploaded Documents:\n{doc_context_tab1}"
            if use_search:
                with st.spinner("Searching web for latest data..."):
                    search_data = web_search(scenario[:100])
                    st.markdown("<div class='search-result'>" + search_data + "</div>", unsafe_allow_html=True)
                    final_scenario += "\n\nRecent web data:\n" + search_data
            with st.spinner(f"{num_agents} BA agent(s) analyzing..."):
                result_str = run_crew(final_scenario, babok_area, num_agents, model_choice, temperature)
                st.session_state.run_count += 1
                st.session_state.history.append({
                    "type": babok_area[:40],
                    "tab": "Requirements",
                    "scenario": scenario[:80] + ("..." if len(scenario) > 80 else ""),
                    "time": datetime.now().strftime("%b %d, %I:%M %p"),
                    "result": result_str,
                    "model": model_choice
                })
            st.success("BA Analysis Complete!")
            st.markdown("<div class='result-box'>" + result_str + "</div>", unsafe_allow_html=True)
            st.download_button("Download Report", data=result_str, file_name=f"ba_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", mime="text/plain")
        else:
            st.warning("Please describe your scenario first!")

with tab2:
    st.markdown("#### Document Analyzer")
    st.markdown("<div style='color:#8b9ab5;font-size:0.9rem;margin-bottom:1rem'>Upload BRDs, SOWs, contracts, meeting notes, process docs, images, Excel, JSON — any business document.</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload Documents", type=["pdf","docx","doc","pptx","png","jpg","jpeg","bmp","tiff","txt","json","xlsx","xls","csv"], accept_multiple_files=True, label_visibility="collapsed")
    analysis_type = st.selectbox("What do you want to extract?", [
        "Extract & Summarize Requirements",
        "Identify Stakeholders",
        "Flag Risks & Assumptions",
        "List Action Items & Decisions",
        "Find Missing Requirements",
        "Full BA Document Review"
    ])
    doc_question = st.text_area("Additional Instructions (optional)", placeholder="E.g. Focus on functional requirements only. Ignore section 3.", height=80)
    if uploaded_files:
        st.markdown("**Uploaded Files:**")
        for f in uploaded_files:
            size_kb = round(f.size / 1024, 1)
            st.markdown(f"<div class='file-preview'>{f.name} - {size_kb} KB</div>", unsafe_allow_html=True)
    if st.button("Analyze Documents", type="primary", key="doc_run"):
        if not uploaded_files:
            st.warning("Please upload at least one file!")
        else:
            with st.spinner("Extracting text from documents..."):
                all_text = ""
                for f in uploaded_files:
                    extracted = extract_text_from_file(f)
                    if extracted:
                        all_text += f"\n\n--- {f.name} ---\n{extracted}"
            if all_text.strip():
                full_scenario = f"Task: {analysis_type}\nAdditional Instructions: {doc_question}\nDocument Content:\n{all_text[:4000]}"
                with st.spinner("Senior BA analyzing documents..."):
                    result_str = run_crew(full_scenario, "Document Analysis Specialist", 1, model_choice, temperature)
                    st.session_state.run_count += 1
                    st.session_state.history.append({
                        "type": "Document Analysis",
                        "tab": "Document",
                        "scenario": analysis_type,
                        "time": datetime.now().strftime("%b %d, %I:%M %p"),
                        "result": result_str,
                        "model": model_choice
                    })
                st.success("Document Analysis Complete!")
                st.markdown("<div class='result-box'>" + result_str + "</div>", unsafe_allow_html=True)
                st.download_button("Download Analysis", data=result_str, file_name=f"doc_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", mime="text/plain")
            else:
                st.error("Could not extract text from uploaded files.")

with tab3:
    st.markdown("#### BA Toolkit")
    st.markdown("<div style='color:#8b9ab5;font-size:0.9rem;margin-bottom:1.5rem'>One-click BA deliverable generators - all BABOK aligned.</div>", unsafe_allow_html=True)
    ba_templates = {
        "User Stories": "Write 5 detailed user stories in INVEST format for a digital transformation project in Ontario, Canada. Include acceptance criteria for each.",
        "Gap Analysis": "Perform a detailed gap analysis for a business switching from manual processes to an ERP system in Ontario. Include AS-IS state, TO-BE state, and gap recommendations.",
        "Stakeholder Register": "Create a complete stakeholder register for implementing a new CRM system at a mid-size business in Ontario. Include interest, influence, and engagement strategy for each stakeholder.",
        "BRD Generator": "Write a Business Requirements Document section for automating payroll processing using Kronos WFM. Include business objectives, scope, assumptions, and functional requirements.",
        "CBAP Practice": "Generate 10 CBAP exam-style scenario questions for the Requirements Life Cycle Management knowledge area with detailed answers and BABOK references.",
        "Process Flow": "Document the AS-IS and TO-BE process flow for a manual invoice approval process being automated with SAP. Include swimlanes, decision points, and improvement recommendations.",
        "Risk Register": "Create a BA risk register for an ERP implementation project. Include risk description, probability, impact, mitigation strategy, and owner for each risk.",
        "Use Case": "Write 3 detailed use cases for an online customer portal. Include actors, preconditions, main flow, alternate flow, and postconditions.",
        "Meeting Notes": "Analyze these meeting notes and extract: key decisions made, action items with owners, open issues, risks identified, and next steps.",
        "Business Case": "Write a mini business case for implementing an AI-powered document management system at a mid-size Canadian company. Include problem statement, options analysis, costs, benefits, and recommendation."
    }
    cols = st.columns(2)
    for idx, (label, prompt) in enumerate(ba_templates.items()):
        with cols[idx % 2]:
            if st.button(label, key=f"ba_{idx}"):
                st.session_state["ba_prefill"] = prompt
                st.rerun()
    st.markdown("---")
    ba_prefill = st.session_state.get("ba_prefill", "")
    ba_scenario = st.text_area("BA Task", value=ba_prefill, height=130, key="ba_input")
    doc_context_tab3 = universal_uploader("tab3")
    if st.button("Generate BA Deliverable", type="primary", key="ba_run"):
        if ba_scenario.strip():
            with st.spinner("CBAP-certified BA agent generating deliverable..."):
                full_ba = ba_scenario
                if doc_context_tab3:
                    full_ba += f"\n\nUploaded Documents:\n{doc_context_tab3}"
                result_str = run_crew(full_ba, "Senior Business Analyst", 1, model_choice, temperature)
                st.session_state.run_count += 1
                st.session_state.history.append({
                    "type": "BA Toolkit",
                    "tab": "BA Toolkit",
                    "scenario": ba_scenario[:80],
                    "time": datetime.now().strftime("%b %d, %I:%M %p"),
                    "result": result_str,
                    "model": model_choice
                })
            st.success("BA Deliverable Ready!")
            st.markdown("<div class='result-box'>" + result_str + "</div>", unsafe_allow_html=True)
            st.download_button("Download Deliverable", data=result_str, file_name=f"ba_deliverable_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", mime="text/plain")
        else:
            st.warning("Please select a template or enter a BA task!")

with tab4:
    st.markdown("#### Session History")
    if not st.session_state.history:
        st.info("No analyses run yet. Start with Requirements Analysis or BA Toolkit!")
    else:
        st.markdown(f"**Total analyses this session: {st.session_state.run_count}**")
        st.markdown("---")
        for i, item in enumerate(reversed(st.session_state.history)):
            run_num = len(st.session_state.history) - i
            with st.expander(f"Run #{run_num} - {item['type']} - {item['time']}"):
                st.markdown(f"**Tab:** {item['tab']} | **Model:** {item.get('model','N/A')}")
                st.markdown(f"**Scenario:** {item['scenario']}")
                st.markdown("**Result:**")
                st.markdown("<div class='result-box'>" + item["result"] + "</div>", unsafe_allow_html=True)
                st.download_button(f"Download Run #{run_num}", data=item["result"], file_name=f"run_{run_num}.txt", mime="text/plain", key=f"dl_{i}")
        if st.button("Clear Session History", key="clear_history"):
            st.session_state.history = []
            st.session_state.run_count = 0
            st.rerun()

st.markdown("""
<div class='footer-box'>
    <strong>BAi Studio</strong> - Your AI-Powered Business Analysis Workspace<br><br>
    Built by <a href='https://www.linkedin.com/in/karthik-reddy-t-666334232/' target='_blank'>Karthik Reddy T</a> - Business Analyst | CBAP Candidate
</div>
""", unsafe_allow_html=True)
