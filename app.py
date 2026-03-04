import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import io

# Настройка страницы
st.set_page_config(page_title="Tender Auditor 44-FZ", layout="centered")

# Функция извлечения текста
def get_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "".join([page.extract_text() for page in reader.pages])
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs])
    return None

# --- ИНТЕРФЕЙС (САЙДБАР) ---
with st.sidebar:
    st.title("🔒 Вход")
    # Проверка пароля через секреты Streamlit
    user_pwd = st.text_input("Пароль доступа", type="password")
    if user_pwd != st.secrets["APP_PASSWORD"]:
        st.error("Доступ запрещен")
        st.stop()
    
    st.success("Доступ разрешен")
    st.divider()
    st.markdown("### Настройки ИИ")
    model_name = st.selectbox("Модель", ["gemini-1.5-flash", "gemini-1.5-pro"])

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("⚖️ Аналитик критериев ЕИС")
st.info("Загрузите файл (PDF/DOCX) или вставьте текст критериев оценки.")

tab1, tab2 = st.tabs(["📂 Загрузка файла", "📝 Вставить текст"])

raw_content = ""

with tab1:
    file = st.file_uploader("Загрузите документацию", type=["pdf", "docx"])
    if file:
        raw_content = get_text_from_file(file)

with tab2:
    text_input = st.text_area("Текст критериев из ЕИС", height=250)
    if text_input:
        raw_content = text_input

if st.button("🚀 Начать анализ на нарушения"):
    if not raw_content:
        st.error("Нет данных для анализа!")
    else:
        with st.spinner("Gemini сверяет данные с 44-ФЗ и ПП 2604..."):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel(model_name)
                
                prompt = f"""
                ТЫ: Юрист-эксперт по закупкам 44-ФЗ.
                ЗАДАЧА: Проверить критерии оценки на соответствие ПП РФ № 2604. 
                ОСОБОЕ ВНИМАНИЕ: Мы — агентство событийного маркетинга. Ищи сужения в опыте, штате и оборудовании.
                
                ДАННЫЕ ДЛЯ АНАЛИЗА:
                {raw_content}
                
                ФОРМАТ ОТВЕТА:
                1. Список выявленных нарушений/рисков.
                2. Обоснование (ссылка на пункт закона).
                3. Резюме: стоит ли подавать жалобу в ФАС?
                """
                
                response = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Ошибка: {e}")
