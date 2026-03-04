import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document
import io
import os

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ (В стиле твоего первого кода) ---
st.set_page_config(page_title="Тендерный Аналитик 2604", layout="wide")

# --- ПОДКЛЮЧЕНИЕ OPENROUTER ---
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=st.secrets["OPENROUTER_API_KEY"],
)

# --- ФУНКЦИИ ПАРСИНГА ---
def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def load_law_context():
    laws_text = ""
    for law_file in ["44fz.txt", "pp2604.txt"]:
        if os.path.exists(law_file):
            try:
                with open(law_file, "r", encoding="utf-8") as f:
                    laws_text += f"\n[ДАННЫЕ ИЗ {law_file}]:\n" + f.read()
            except Exception as e:
                st.sidebar.error(f"Ошибка чтения {law_file}: {e}")
    return laws_text

def create_docx(report_text):
    doc = Document()
    doc.add_heading('Отчет об аудите критериев (44-ФЗ / ПП 2604)', 0)
    doc.add_paragraph(report_text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- САЙДБАР С ПАРОЛЕМ (Как в первом коде) ---
with st.sidebar:
    st.title("🔐 Доступ")
    password = st.text_input("Введите пароль", type="password")
    if password != st.secrets["APP_PASSWORD"]:
        st.error("Доступ ограничен")
        st.stop()
    st.success("Доступ разрешен")
    st.divider()
    st.info("Анализ на базе 44-ФЗ и ПП РФ № 2604")

# --- ИНТЕРФЕЙС (Возвращаем 1-й вариант: Колонки и Радио-кнопки) ---
st.title("🚀 Анализ критериев ЕИС на законность")

col1, col2 = st.columns([1, 1])

with col1:
    option = st.radio("Способ загрузки:", ("Текст", "Документ (PDF/Docx)"))
    input_text = ""
    
    if option == "Текст":
        input_text = st.text_area("Вставьте текст критериев здесь...", height=400)
    else:
        uploaded_file = st.file_uploader("Загрузите файл с критериями", type=["pdf", "docx"])
        if uploaded_file:
            if uploaded_file.name.endswith(".pdf"):
                input_text = extract_text_from_pdf(uploaded_file)
            else:
                input_text = extract_text_from_docx(uploaded_file)
            st.success("Текст извлечен!")

with col2:
    st.subheader("Результат анализа")
    if st.button("⚖️ Проверить на нарушения", use_container_width=True):
        if not input_text:
            st.warning("Сначала введите данные!")
        else:
            with st.spinner("OpenRouter связывается с Gemini и сверяет законы..."):
                try:
                    legal_context = load_law_context()
                    
                    # --- ТВОЙ ПРОМТ (БЕЗ ИЗМЕНЕНИЙ) ---
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
                    
                    # Исправленный вызов API
                    response = client.chat.completions.create(
                        model="anthropic/claude-3.5-sonnet",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
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
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Произошла ошибка: {e}")

st.divider()
st.caption("Тендерный отдел | Анализ на основе ИИ")
