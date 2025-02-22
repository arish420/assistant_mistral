import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
import getpass
import os
from PyPDF2 import PdfReader
import sentence_transformers
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
###############################################################################################
files=os.listdir()
###############################################################################################
files=[file for file in files if file.split(".")[-1]=="pdf"]
###############################################################################################
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text
text_data=get_pdf_text(files)




# # split the extracted data into text chunks using the text_splitter, which splits the text based on the specified number of characters and overlap
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
text_chunks = text_splitter.split_text(text_data)
# print the number of chunks obtained
# len(text_chunks)



modelPath = "BAAI/bge-large-en-v1.5"

# Create a dictionary with model configuration options, specifying to use the CPU for computations
model_kwargs = {'device':'cpu'}
#if using apple m1/m2 -> use device : mps (this will use apple metal)

# Create a dictionary with encoding options, specifically setting 'normalize_embeddings' to False
encode_kwargs = {'normalize_embeddings': True}

# Initialize an instance of HuggingFaceEmbeddings with the specified parameters
embeddings = HuggingFaceEmbeddings(
    model_name=modelPath,     # Provide the pre-trained model's path
    model_kwargs=model_kwargs, # Pass the model configuration options
    encode_kwargs=encode_kwargs # Pass the encoding options
)

# Convert text_chunks (list of strings) to Document objects
documents = [Document(page_content=chunk) for chunk in text_chunks]  

# Now use 'documents' instead of 'text_chunks'
vector_store = FAISS.from_documents(documents=documents, embedding=embeddings)

# Retrieve and generate using the relevant snippets of the blog.
retriever = vector_store.as_retriever()

GROQ_API_KEY=os.getenv("GROQ_API_KEY")

from langchain_groq import ChatGroq

llm = ChatGroq(
    temperature=0,
    model="mixtral-8x7b-32768",
    api_key=GROQ_API_KEY
)

prompt = hub.pull("rlm/rag-prompt")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

st.title("Student Assistant")

query=st.text_input("Write Query Here")


if st.button("Submit") and res!="":
    res=rag_chain.invoke(query)
    st.write(res)

    # # performing a similarity search to fetch the most relevant context
    st.write("")
    st.write("")
    st.write("")
    
    st.write(vector_store.similarity_search(query))


