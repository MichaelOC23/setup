

import ollama
import chromadb
import uuid
from langchain.schema import Document

class Ollama_LLM:
    
    def __init__(self):
        """
        Initializes the TavilySearch object
        Args:
            query:
        """
        self.system_prompt = "I am a highly intelligent question answering system. If you have any questions you can ask me."
        self.user_prompt = ""
        self.chroma_embedding_collection_name = "docs"
        self.embedding_model = "mxbai-embed-large"
        self.embeddings = []
        self.chroma_persist_directory = 'chroma/'
        self.client = chromadb.Client()
        self.collection = None
          
        
    def embed_documents(self, docs, embeddings_model="mxbai-embed-large", collection_name="docs"):

        # get the collection
        collection = self.get_collection(collection_name)
        
        if isinstance(docs, str):
            doc_list = [docs]
        elif isinstance(docs, dict):
            doc_list = {str(i): d for i, d in enumerate(docs)}
        else:
            doc_list = docs
        
        # store each document in a vector embedding database
        for d in doc_list:
            if isinstance(d, Document):
                d = d.page_content
            
            response = ollama.embeddings(model=embeddings_model, prompt=d)
            
            embedding = response["embedding"]
            
            collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                documents=[d]
            )
        self.collection = collection
    
    def get_collection(self, collection_name):
        try:
            return self.client.get_collection(name=collection_name)
        except:
            return self.client.create_collection(name=collection_name)
    
    def retrieve_embedding(self, prompt="", embeddings_model="mxbai-embed-large", collection_name="docs", n_results=50):
        
        if not prompt:
            prompt = self.system_prompt
        else:
            self.user_prompt = prompt
        
        # get the collection
        collection = self.collection or self.get_collection(collection_name)
        
        # generate an embedding for the prompt and retrieve the most relevant doc
        response = ollama.embeddings(prompt=prompt, model=embeddings_model)
        
        # query the collection using the embedding of the prompt
        new_embeddings = collection.query(query_embeddings=[response["embedding"]], n_results=n_results)
        self.embeddings = new_embeddings
        return new_embeddings
    
    def generate_response(self, prompt="", model = "llama2"):
        
        self.retrieve_embedding(prompt, self.embedding_model, self.chroma_embedding_collection_name)
        
        # generate a response combining the prompt and data we retrieved in step 2
        output = ollama.generate(model=model,
            prompt=f"Using this data: {self.embeddings}. Respond to this prompt: Create a professional profile for: {prompt}")
        
        return output
