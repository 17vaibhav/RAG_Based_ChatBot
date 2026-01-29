# 📄 RAG on Your Uploaded PDF

A production-ready Streamlit application that enables Retrieval-Augmented Generation (RAG) on PDF documents. It primarily leverages **Docling** for intelligent document chunking, **Google Gemini** for embeddings and reasoning, and **ChromaDB** for local vector storage.

---

## 🏗️ Architecture

```ascii
+-------------------+       +-------------------+       +-------------------+
|  User Upload PDF  | ----> |     Streamlit     | ----> |    Docling Parse  |
+-------------------+       |    Frontend UI    |       |   & Text Chunking |
                            +-------------------+       +-------------------+
                                      |                           |
                                      |                           v
                            +-------------------+       +-------------------+
                            |   Gemini 1.5 LLM  | <---- | Google Embeddings |
                            |  (Answer Gen)     |       | (text-embedding-004)|
                            +-------------------+       +-------------------+
                                      ^                           |
                                      |                           v
                            +-------------------+       +-------------------+
                            |  Context Retrieval| <---- |     ChromaDB      |
                            |   (Top k Chunks)  |       |   (Vector Store)  |
                            +-------------------+       +-------------------+
```

---

## ✨ Features

- **Upload & Process**: Securely upload PDF documents.
- **Intelligent Parsing**: Uses `Docling` to accurately extract text and structure from PDFs.
- **Vector Search**: Stores embeddings locally using `ChromaDB` for fast retrieval.
- **State-of-the-Art Models**:
  - Embeddings: `text-embedding-004`
  - LLM: `gemini-2.5-flash`
- **Interactive Chat**: Ask questions and get context-aware answers in real-time.
- **User Authentication**: Simple ID-based login for personalized experiences.
- **Session Management**: Create multiple chat sessions, resume previous ones, and view chat history.

---

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Document Processing**: [Docling](https://github.com/DS4SD/docling)
- **Vector Store**: [ChromaDB](https://www.trychroma.com/)
- **LLM Integration**: [LangChain](https://www.langchain.com/)
- **AI Models**: Google Gemini via `langchain-google-genai`
- **Session Storage**: [SQLite](https://www.sqlite.org/index.html)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ (3.12.7 used in this project)
- A Google Cloud API Key (for Gemini)

### Installation

1. **Clone the repository** (if you haven't already):

   ```bash
   git clone <your-repo-url>
   cd RAG_Based_ChatBot
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment**:
   Create a `.env` file in the root directory and add your API Key:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   ```

### Running the App

```bash
streamlit run app.py
```

The app will launch in your browser at `http://localhost:8501`.

### 🕹️ Usage Guide

1. **Login**: Enter a unique User ID and your Display Name.
2. **Session Dashboard**:
   - **Start New Session**: Enter a name for your chat (or let it auto-generate) and click "Create & Start".
   - **Resume Session**: Pick from your list of previous conversations to pick up where you left off.
3. **Chat Interface**:
   - Upload a PDF (or use the one already in the DB if checked).
   - Ask questions!
   - Use the sidebar to **Switch Session** or **Logout**.

---

## 📂 Project Structure

```text
RAG_Based_ChatBot/
├── app.py               # Streamlit Frontend Application
├── rag_engine.py        # Core RAG Logic (Backend)
├── session_manager.py   # Session & User Management Logic
├── requirements.txt     # Project Dependencies
├── create_sample_pdf.py # Utility to create testing PDF
├── sample_rag_IPL.pdf   # Sample PDF 1
├── sample_rag_chess.pdf # Sample PDF 2
├── sessions.db          # SQLite User/Session Database (Runtime)
└── chroma_db/           # Local Vector Database (Runtime)
```

---

## 🤝 Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

**Maintained by**: Vaibhav Amrit
