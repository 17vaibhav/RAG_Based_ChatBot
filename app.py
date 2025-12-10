import streamlit as st
import os
from rag_engine import RAGEngine, save_uploaded_file
from loguru import logger

# Page Config
st.set_page_config(page_title="Docling RAG Chat", layout="wide")
logger.info("App started")

# Title
st.title("RAG on Your Uploaded PDF by VAIBHAV AMRIT")

# Sidebar for Config
with st.sidebar:
    st.header("Configuration")
    
    # API Key Handling, uncomment if want api key from user input
    # api_key_input = st.text_input("Google API Key", type="password", help="Enter your Gemini API key")
    
    # Priority: Input field -> Env Var
    # api_key = api_key_input or os.getenv("GOOGLE_API_KEY") # Uncomment if 'api_key_input' is used
    try : 
        api_key = os.getenv("GOOGLE_API_KEY")
        logger.info("API key loaded successfully")
    except Exception as e:
        logger.error(f"Error getting API key: {e}")
    
    st.divider()
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload your PDF to do RAG", type=["pdf"])
    logger.info(f"Uploaded file: {uploaded_file}")
    
    process_button = st.button("Process your PDF", type="primary", disabled=not uploaded_file)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None

# Logic
if process_button and uploaded_file and api_key:
    with st.spinner("Processing your PDF with Docling..."):
        try:
            # save file
            temp_path = save_uploaded_file(uploaded_file)
            logger.info(f"Temp file saved: {temp_path}")
            
            # init engine
            engine = RAGEngine(google_api_key=api_key)
            engine.process_pdf(temp_path)
            
            # store in session
            st.session_state.rag_engine = engine
            st.success("Your PDF Processed & Embeddings Stored! ASK YOUR QUESTIONS!")
            logger.info("PDF processed & embeddings stored successfully")
            
            # clean up temp file (optional, keeping simple for now)
            # os.remove(temp_path) 
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            st.error(f"Error processing file: {e}")

# Chat Interface
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask a question about your PDF...")
if prompt :
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if not st.session_state.rag_engine and not api_key:
         with st.chat_message("assistant"):
            st.error("Please provide an API Key and process a PDF first.")
    else:            
        # Generate response
        try:
            # Re-init engine if lost (e.g. reload but db exists) or use existing
            engine = st.session_state.rag_engine
            if not engine:
                 engine = RAGEngine(google_api_key=api_key)
            
            with st.chat_message("assistant"):
                 with st.spinner("Thinking..."):
                    response = engine.get_answer(prompt)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"Error generating answer: {e}")
