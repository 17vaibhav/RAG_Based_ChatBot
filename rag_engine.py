import os
import tempfile
import hashlib
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



    def calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _load_vector_store(self):
        """Lazy load or reload the vector store"""
        if not self.vector_store:
            # Check if directory exists first to avoid creating empty db on just check
            if os.path.exists(self.vector_store_path):
                 self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )
            # If not exist, it will be created in process_pdf

    def process_pdf(self, file_path: str) -> bool:
        """
        Processes a PDF file. returns True if new file processed, False if already existed.
        """
        # 1. Calculate Hash
        file_hash = self.calculate_hash(file_path)
        
        # 2. Check if already exists in DB
        self._load_vector_store()
        
        if self.vector_store:
             # Look for any document with this hash
             existing_docs = self.vector_store.get(where={"source_hash": file_hash}, limit=1)
             if len(existing_docs['ids']) > 0:
                 logger.info(f"PDF with hash {file_hash} already exists in vector store. Skipping processing.")
                 return False

        # 3. Only if not exists: Convert, Chunk, Embed
        logger.info(f"Processing new PDF: {file_path}")
        result = self.doc_converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.create_documents([markdown_text])
        
        # Add metadata including hash
        for chunk in chunks:
            chunk.metadata["source_hash"] = file_hash
            # We use filename instead of full temp path for cleaner source
            chunk.metadata["source"] = os.path.basename(file_path)
            
        logger.info(f"Created {len(chunks)} chunks for new file")

        # 4. Create/Update Vector Store
        if self.vector_store:
            self.vector_store.add_documents(chunks)
        else:
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.vector_store_path
            )
        logger.info("Vector store updated successfully")
        return True

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
            """
            <role>
            You are an assistant designed specifically for accurate question answering.
            </role>

            <context_handling>
            Use the retrieved context provided in the variable {context} to answer the question.  
            If the context does not contain enough information, respond with I don't know.  
            Do not guess or invent details.
            </context_handling>

            <output_rules>
            Provide the answer in a maximum of three sentences.  
            Keep the response concise, direct, and clear.  
            Avoid unnecessary elaboration.
            </output_rules>

            <instruction>
            Always rely strictly on the given context when forming answers.
            </instruction>
            """
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
