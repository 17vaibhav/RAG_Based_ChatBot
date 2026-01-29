import streamlit as st
import os
from rag_engine import RAGEngine, save_uploaded_file
import session_manager
from loguru import logger

# Initialize DB
session_manager.init_db()

# Page Config
st.set_page_config(page_title="RAG ChatBot", layout="wide")
logger.info("App started")

# --- Session State Management ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None  # {user_id, user_name}
if "current_session" not in st.session_state:
    st.session_state.current_session = None # Full session dict
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None

# --- Login UI ---
if not st.session_state.user_info:
    st.title("Welcome to RAG ChatBot")
    st.markdown("Please sign in to continue.")
    
    with st.form("login_form"):
        user_id = st.text_input("User ID (Unique)", placeholder="e.g., user123")
        user_name = st.text_input("Display Name", placeholder="e.g., Vaibhav")
        submit_login = st.form_submit_button("Sign In")
        
        if submit_login and user_id and user_name:
            st.session_state.user_info = {"user_id": user_id, "user_name": user_name}
            st.rerun()
            
    st.stop()

# --- Session Selection UI ---
if not st.session_state.current_session:
    user = st.session_state.user_info
    st.title(f"Hello, {user['user_name']}!")
    st.subheader("Select a Session")
    
    # 1. Create New Session
    with st.expander("Start New Session", expanded=True):
        with st.form("new_session_form"):
            new_session_name = st.text_input("Session Name (Optional)", placeholder="My RAG Chat")
            create_btn = st.form_submit_button("Create & Start")
            
            if create_btn:
                session = session_manager.create_session(user["user_id"], user["user_name"], new_session_name)
                if session:
                    st.session_state.current_session = session
                    st.session_state.messages = [] # New session empty
                    st.rerun()
    
    # 2. List Previous Sessions
    sessions = session_manager.get_user_sessions(user["user_id"])
    if sessions:
        st.write("### Previous Sessions")
        for sess in sessions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{sess['session_name']}**")
                st.caption(f"Last active: {sess['last_interaction']}")
            with col2:
                if st.button("Resume", key=sess['session_id']):
                    full_session = session_manager.get_session(sess['session_id'])
                    st.session_state.current_session = full_session
                    st.session_state.messages = full_session.get("chat_history", [])
                    st.rerun()
    else:
        st.info("No previous sessions found.")
        
    if st.button("Logout"):
        st.session_state.user_info = None
        st.rerun()
        
    st.stop()

# --- Main App (Active Session) ---
session = st.session_state.current_session
user = st.session_state.user_info

# Sidebar Info & Controls
st.sidebar.markdown(f"**User:** {user['user_name']}")
st.sidebar.markdown(f"**Session:** {session['session_name']}")

if st.sidebar.button("Switch Session"):
    st.session_state.current_session = None
    st.session_state.messages = []
    st.session_state.rag_engine = None # Reset engine on switch
    st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.user_info = None
    st.session_state.current_session = None
    st.session_state.messages = []
    st.rerun()

# Title
st.title("RAG ChatBot by VAIBHAV AMRIT")

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


# Logic
if process_button and uploaded_file and api_key:
    with st.spinner("Processing your PDF with Docling..."):
        try:
            # save file
            temp_path = save_uploaded_file(uploaded_file)
            logger.info(f"Temp file saved: {temp_path}")
            
            # init engine
            engine = RAGEngine(google_api_key=api_key)
            is_new_file = engine.process_pdf(temp_path)
            
            # store in session
            st.session_state.rag_engine = engine
            if is_new_file:
                st.success("Your PDF Processed & Embeddings Stored! ASK YOUR QUESTIONS!")
                logger.info("New PDF processed & embeddings stored successfully")
            else:
                st.info("PDF already uploaded previously. Loaded from existing database! ASK YOUR QUESTIONS!")
                logger.info("PDF loaded from existing vector store")
            
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
    # Persist user message
    session_manager.update_chat_history(session['session_id'], st.session_state.messages)
    
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
            # Persist assistant message
            session_manager.update_chat_history(session['session_id'], st.session_state.messages)
            
        except Exception as e:
            st.error(f"Error generating answer: {e}")
