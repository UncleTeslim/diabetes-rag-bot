from src.helpers import load_file, text_splitter, download_embeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv


load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

extracted_data= load_file(data = 'data/')
texts_chunks = text_splitter(data=extracted_data)
embeddings = download_embeddings()




from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key= PINECONE_API_KEY)


index_name =  "diabetesbot"

# pc.create_index(
#     name=index_name,
#     dimension=384, 
#     metric="cosine",
#     spec=ServerlessSpec(
#         cloud="aws",
#         region="us-east-1"
#     ) 
# )


# #Load existing index

from langchain_pinecone import PineconeVectorStore

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
)


docsearch = PineconeVectorStore.from_documents(
    documents=texts_chunks,
    index_name=index_name,
    embedding=embeddings,
)