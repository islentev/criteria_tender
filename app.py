import streamlit as st
from openai import OpenAI # Используем универсальный клиент
from PyPDF2 import PdfReader
from docx import Document
import io
import os

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=st.secrets["OPENROUTER_API_KEY"],
)

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Tender Auditor AI", layout="wide")

# --- ФУНКЦИИ ОБРАБОТКИ ТЕКСТА ---
def get_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "".join([page.extract_text() or "" for page in reader.pages])
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs])
    return None

def load_law_context():
    laws_text = ""
    # Ищем файлы в корне репозитория (важно: загрузите их на GitHub как .pdf или .txt)
    for law_file in ["44fz.pdf", "pp2604.pdf"]:
        if os.path.exists(law_file):
            try:
                reader = PdfReader(law_file)
                laws_text += f"\n[ДАННЫЕ ИЗ {law_file}]:\n"
                # Берем ключевые страницы (например, первые 50), чтобы не перегружать контекст
                for page in reader.pages[:50]:
                    laws_text += page.extract_text() or ""
            except Exception as e:
                st.sidebar.error(f"Ошибка загрузки {law_file}: {e}")
    return laws_text

def create_docx(report_text):
    doc = Document()
    doc.add_heading('Отчет об аудите тендерной документации', 0)
    doc.add_paragraph(report_text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- АВТОРИЗАЦИЯ ---
with st.sidebar:
    st.title("🔐 Доступ")
    pwd = st.text_input("Пароль", type="password")
    if pwd != st.secrets["APP_PASSWORD"]:
        st.error("Введите верный пароль")
        st.stop()
    
    st.success("Доступ разрешен")
    st.divider()
    st.info("Приложение сверяет критерии заказчика с 44-ФЗ и ПП РФ № 2604.")

# --- ИНТЕРФЕЙС ---
st.title("🚀 AI-Аналитик: Проверка законности критериев")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Ввод данных")
    source = st.radio("Как передать критерии?", ["Загрузить файл", "Вставить текст"])
    
    input_text = ""
    if source == "Загрузить файл":
        file = st.file_uploader("Выберите PDF или DOCX", type=["pdf", "docx"])
        if file:
            input_text = get_text_from_file(file)
    else:
        input_text = st.text_area("Вставьте текст критериев оценки из ЕИС...", height=300)

with col2:
    st.subheader("Результат анализа")
    if st.button("⚖️ Проверить на нарушения"):
        if not input_text:
            st.warning("Пожалуйста, предоставьте текст для анализа.")
        else:
            with st.spinner("OpenRouter связывается с Gemini..."):
                try:
                    legal_context = load_law_context()
                    
                    prompt = f"""
                    Ты — ведущий эксперт по тендерному праву. Сравни критерии заказчика с законом.
                    
                    ЭТАЛОННЫЕ ЗАКОНЫ:
                    {legal_context}
                    
                    КРИТЕРИИ ЗАКАЗЧИКА:
                    {input_text}
                    
                    ИНСТРУКЦИЯ:
                    1. В самом начале напиши жирным шрифтом: "СТАТУС: ЗАМЕЧАНИЯ ВЫЯВЛЕНЫ" или "СТАТУС: ЗАМЕЧАНИЙ НЕ ВЫЯВЛЕНО".
                    2. Если нарушения есть, перечисли их по пунктам:
                       - Суть нарушения.
                       - Ссылка на статью (44-ФЗ или ПП 2604).
                       - Текст для жалобы в ФАС.
                    3. Если нарушений нет, кратко подтверди соответствие.
                    
                    Отвечай на русском языке.
                    """
                    
                    response = client.chat.completions.create(
                      model="google/gemini-flash-1.5", 
                    report_content = response.choices[0].message.content
                    
                    # 1. Вывод отчета в окно
                    st.markdown(report_content)
                    
                    # 2. Создание и кнопка скачивания DOCX
                    docx_file = create_docx(report_content)
                    st.divider()
                    st.download_button(
                        label="📄 Скачать отчет в Word (.docx)",
                        data=docx_file,
                        file_name="Audit_Report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Произошла ошибка: {e}")
       
