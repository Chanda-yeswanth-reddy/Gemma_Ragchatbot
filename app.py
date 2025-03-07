import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Load API keys
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")

st.title("Gemma Chatbot")

# Initialize LLM
llm = ChatGroq(groq_api_key=groq_api_key, model="gemma2-9b-it")

# Ensure prompt has 'context' as required
prompt = ChatPromptTemplate.from_template("""
Answer the questions based on the provided context only.
Please provide the most accurate response based on the question.

<context>
{context}
</context>

Question: {input}
""")

# Function to create vector embeddings
def vector_embedding():
    if "vectors" not in st.session_state:
        st.session_state.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        st.session_state.loader = PyPDFDirectoryLoader("./pdfs")
        st.session_state.docs = st.session_state.loader.load()
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs)
        
        
        st.session_state.vectors = FAISS.from_documents(
            st.session_state.final_documents, 
            embedding=st.session_state.embeddings
        )
        
        st.write("✅ Vector store DB is ready!")


# Button to create vector store
if st.button("Create Vector Store"):
    vector_embedding()

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input for chatbot
prompt1 = st.text_input("What do you want to ask?")

# Process query when user clicks "Ask"
if st.button("Ask"):
    if "vectors" not in st.session_state:
        st.write("⚠ Please create the vector store first!")
    elif prompt1:
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        response = retrieval_chain.invoke({'input': prompt1})
        answer = response['answer']

        # Save question and answer in chat history
        st.session_state.chat_history.append({"question": prompt1, "answer": answer})

        # Display the answer
        st.write(answer)

# Display previous chat history
st.subheader("Chat History")
for chat in st.session_state.chat_history:
    st.write(f"**Q:** {chat['question']}")
    st.write(f"**A:** {chat['answer']}")
    st.write("---")
