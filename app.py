import streamlit as st
from groq import Groq
from datetime import datetime
import fitz
from docx import Document
from pptx import Presentation
import os

st.set_page_config(page_title="BAi Studio", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")
