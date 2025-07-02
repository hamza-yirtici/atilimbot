from langchain_core.prompts.prompt import PromptTemplate
from langsmith.evaluation import LangChainStringEvaluator
from dotenv import load_dotenv
import os
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_qdrant import Qdrant
import qdrant_client
from langsmith.evaluation import evaluate

load_dotenv()

_PROMPT_TEMPLATE = """Please grade the predicted answer to the question.
This is the question:
{query}
Here is the real answer:
{answer}
You are grading the following predicted answer:
{result}
Respond with CORRECT or INCORRECT. If the predicted answer says it doesn't know respond with INCORRECT.
If the predicted answer says information is not provided respond with INCORRECT.
Grade:
"""

PROMPT = PromptTemplate(
    input_variables=["query", "answer", "result"], template=_PROMPT_TEMPLATE
)
eval_llm = ChatOpenAI(model="gpt-4o")

qa_evaluator = LangChainStringEvaluator("qa", config={"llm": eval_llm, "prompt": PROMPT})

def my_app(question):
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

    llm = ChatOpenAI(model="gpt-4o")
    memory = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
        memory=memory,
    )

    response = chain({'question': question})
    return response["answer"]

def langsmith_app(inputs):
    output = my_app(inputs["question"])
    return {"output": output}

experiment_results = evaluate(
    langsmith_app,
    data="Course dates",
    evaluators=[qa_evaluator],
    experiment_prefix="openai-4o",
)