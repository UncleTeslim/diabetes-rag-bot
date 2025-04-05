from src.helpers import load_file, text_splitter, download_embeddings
from src.prompt import *
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from langchain.document_loaders import PyPDFLoader, DirectoryLoader 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
import os
# from rag_pipeline import rag_query  # your function that takes a question and returns the answer

app = Flask(__name__, static_folder="static", template_folder="templates")

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

embeddings = download_embeddings()

index_name =  "diabetesbot"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
)

retriever = docsearch.as_retriever(search_type="similarity",search_kwargs={"k": 3})
llm = OpenAI(temperature=0.4,max_tokens=500)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")

    print(f"User question:", question)

    response = rag_chain.invoke({"input": question})
    answer = response["answer"].replace("System:", "DiabeticBot:")

    print(f"DiabeticBot response: {answer}")
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)


# @app.route("/ask", methods=["POST"])
# def ask():
#     try:
#         data = request.get_json()
#         print("Received data:", data)

#         question = data.get("question")
#         if not question:
#             return jsonify({"answer": "⚠️ Please provide a question."}), 400
        
#         print("User question:", question)
        
#         result = rag_chain.invoke({"input": question})
#         print("RAG result:", result)

#         return jsonify({"answer": result["answer"]})

#     except Exception as e:
#         import traceback
#         traceback.print_exc()  # This prints the full error in the terminal
#         return jsonify({"answer": "⚠️ Something went wrong.", "error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080, debug=True)