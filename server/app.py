from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_qdrant import Qdrant
import qdrant_client
import uuid
from langsmith import Client
from langsmith import traceable

def get_vector_store():
    client = qdrant_client.QdrantClient(
        os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    embeddings = OpenAIEmbeddings()
    vector_store = Qdrant(
        client=client, 
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"), 
        embeddings=embeddings,
    )
    return vector_store

def get_chain(vector_store):
    llm = ChatOpenAI(model="gpt-4o")
    memory = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
        memory=memory,
        verbose=True
    )
    return chain

@traceable
def get_response(question):
    response = chain({'question': question})
    return response["answer"]

app = Flask(__name__)
CORS(app)

@app.post("/chat")
def chat():
    text = request.get_json().get("message")
    run_id = str(uuid.uuid4())
    response = get_response(text, langsmith_extra={"run_id": run_id})
    message = {"answer": response, "run_id": run_id}
    return jsonify(message)

@app.post("/refresh")
def refresh():
    global chain
    chain = get_chain(vector_store)
    print ("\n\n----------CHAIN REFRESHED SUCCESSFULLY----------\n\n")
    return jsonify({"message": "Chain refreshed successfully"}), 200

@app.post("/feedback")
def feedback():
    score = request.get_json().get("score")
    run_id = request.get_json().get("run_id")
    ls_client.create_feedback(
        run_id,
        key="user-score",
        score=score,)
    print ("\n\n----------FEEDBACK RECORDED SUCCESSFULLY----------\n\n")
    return jsonify({"message": "Feedback recorded successfully"}), 200

if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path)
    vector_store = get_vector_store()
    chain = get_chain(vector_store)
    ls_client = Client()
    app.run(debug=True)