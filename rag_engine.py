import os
import tempfile
from loguru import logger
from docling.document_converter import DocumentConverter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables if .env exists
from dotenv import load_dotenv
load_dotenv()

class RAGEngine:
    def __init__(self, google_api_key: str = None):
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key is required")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.api_key
        )
        self.vector_store_path = "./chroma_db"
        self.vector_store = None
        self.doc_converter = DocumentConverter()

    def process_pdf(self, file_path: str) -> None:
        """
        Processes a PDF file using Docling, chunks the text, and serves it to ChromaDB.
        Assumes PDF contains text (no OCR needed for images).
        """
        # 1. Convert PDF to text using Docling
        # Docling is powerful, but for simple text RAG we primarily need the markdown/text output
        logger.info(f"Processing PDF: {file_path}")
        result = self.doc_converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()
        
        # 2. Chunk text
        # Using RecursiveCharacterTextSplitter for robust chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create langchain Document objects
        # We could also use docling's native chunking if desired, but this is standard LangChain flow
        chunks = text_splitter.create_documents([markdown_text])
        logger.info(f"Created {len(chunks)} chunks")

        # 3. Create Vector Store
        # Persistent ChromaDB
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.vector_store_path
        )
        logger.info("Vector store created successfully")

    def get_answer(self, question: str) -> str:
        """
        Retrieves context and answers the question using Gemini.
        """
        if not self.vector_store:
            # Try loading existing db if not in memory
            if os.path.exists(self.vector_store_path):
                 self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )
            else:
                return "Please upload a document first."

        # Setup LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=self.api_key
        )

        # Retrieval Chain
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({"input": question})
        return response["answer"]

def save_uploaded_file(uploaded_file):
    """Helper to save uploaded streamlit file to temp"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        logger.error(e)
        return None
