import psycopg2
from lmstudio_llama import CustomEmbedding, CustomLLamaLLM

def get_connection(): 
    # Database connection
    conn = psycopg2.connect(
        dbname="knowledge_base_db",
        user="data_pgvector_user",
        password="data_pgvector_password",
        host="localhost",
        port="5435"
    )
    return conn

# embeddings = CustomEmbedding("text-embedding-nomic-embed-text-v1.5@q8_0")
embeddings = CustomEmbedding("text-embedding-nomic-embed-text-v1.5@q8_0")
qwen3_8b = "qwen3-8b"

conn = get_connection()

llm = CustomLLamaLLM(llama_model=qwen3_8b)