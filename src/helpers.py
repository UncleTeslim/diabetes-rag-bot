import os

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_file(data):
    """
    Loads a PDF file from the given path and return the documents.
    """
    loader= DirectoryLoader(data,
                            glob="**/*.pdf", 
                            loader_cls=PyPDFLoader)
    documents = loader.load()
    
    return documents

#
def text_splitter(data):
    """
    Splits the documents into smaller chunks for processing.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
        length_function=len
    )
    texts_chunks = text_splitter.split_documents(data)
    
    return texts_chunks



def download_embeddings():
    """
    Returns OpenAI text-embedding-3-small (1536-dim).
    Uses the OPENAI_API_KEY env var — no local model, no torch.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    return embeddings
