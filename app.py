from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session
import secrets
import os

from src.helpers import download_embeddings
from src.prompt import *

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate


from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from typing import Dict
import uuid
import secrets

set_llm_cache(InMemoryCache())
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# secrets.token_hex(32)
# print(secrets.token_hex(32))

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY


app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "secretkeyfallback")

#Initiate LLM
llm = ChatOpenAI(
    temperature=1.0, 
    model="gpt-4.1-mini",
    openai_api_key=OPENAI_API_KEY,
    max_tokens=2000
    )


#Embeddings
embeddings = download_embeddings()

index_name =  "diabetesbot"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
)

retriever = docsearch.as_retriever(search_type="similarity",search_kwargs={"k": 3})


#LangGraph Workflow
graph = StateGraph(state_schema=MessagesState)

def call_model(state: MessagesState) -> Dict:
    """
    Calls the model with the given state and input.
    """
    system_msg = SystemMessage(content=system_prompt)
    messages = [system_msg] + state['messages'] 
    response = llm.invoke(messages)
    return{"messages": [response]}

graph.add_node("model", call_model)
graph.add_edge(START, "model")
graph.add_edge("model", END)


memory = MemorySaver()
workflow = graph.compile(checkpointer=memory)


#RAG
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])
question_answer_chain = create_stuff_documents_chain(llm,prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=["GET", "POST"])
def ask():

    if request.method == "GET":
        return render_template('ask.html')
    
    
    data = request.get_json()
    question = data.get("question")

    print(f"User question:", question)

    #Create user session if it doesn't exist or fetch existing session
    if "session_id" not in session:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
    else:
        session_id = session["session_id"]
        
    response = workflow.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": session_id}},
    )
    
   
    if isinstance(response, dict) and 'messages' in response:
        bot_message = response['messages'][-1].content
    else:
        bot_message = "⚠️ Sorry, I couldn't retrieve a valid answer. Please try again."

    # Add bonus tip if needed
    if "Note: This answer is based on general knowledge" not in bot_message:
        bot_message += "\n\nBonus Tip: Please remember to always consult with a healthcare provider for any medical advice."

    print(f"Bot response: {bot_message}")
    return jsonify({"response": bot_message})
   

if __name__ == "__main__":
    app.run(host="0.0.0.0" , port=int(os.environ.get("PORT", 10000)))