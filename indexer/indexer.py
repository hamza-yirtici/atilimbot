from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv
import qdrant_client
import os
from PyPDF2 import PdfReader # type: ignore

def get_vector_store():
    client = qdrant_client.QdrantClient(
        os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=300
    )
    embeddings = OpenAIEmbeddings()
    vector_store = Qdrant(
        client=client, 
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"), 
        embeddings=embeddings,
    )
    return vector_store

def get_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

if __name__ == "__main__" :
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path)
    vectorstore = get_vector_store()
    import os
    base_dir = os.path.dirname(__file__)
    directory = os.path.join(base_dir, "indexer", "documents")
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if file.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif file.endswith('.pdf'):
            text = get_text(file_path)
        chunks = get_chunks(text)
        vectorstore.add_texts(chunks)
        print(f"\n{file} added.\n")
        chunks = []
        text = ""
    print("Indexed successfully.")