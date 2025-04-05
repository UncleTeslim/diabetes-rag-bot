from langchain.document_loaders import PyPDFLoader, DirectoryLoader 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings



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
    Downloads the embeddings model from Hugging Face.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        # model_kwargs={"device": "cuda"}
    )
    return embeddings
