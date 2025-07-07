
from llama_index.llms.ollama import Ollama
import os
from llama_index.llms.huggingface import (
    HuggingFaceInferenceAPI,
    HuggingFaceLLM,
)
from typing import List, Optional
from langchain.embeddings.huggingface import HuggingFaceBgeEmbeddings
import llama_index.core
from llama_parse import LlamaParse  #
from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.openai import OpenAI

Settings.embed_model = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en-v1.5")

HF_TOKEN: Optional[str] = os.getenv("YOUR-KEY")
os.environ['COHERE_API_KEY'] = 'YOUR-KEY'
os.environ["OPENAI_API_KEY"] = "YOUR-KEY"
os.environ["ANTHROPIC_API_KEY"] = "YOUR-KEY"


parser = LlamaParse(
    api_key="YOUR-KEY",  # can also be set in your env as LLAMA_CLOUD_API_KEY
    result_type="markdown"  # "markdown" and "text" are available
)

# llm = HuggingFaceInferenceAPI(
#     model_name="google/gemma-2-27b-it",token=HF_TOKEN
# )

# llm_sql = Anthropic(model="claude-3-sonnet-20240229")

# llm = OpenAI(temperature=0.1,model="gpt-3.5-turbo")

# llm_sql = OpenAI(temperature=0.1,model="gpt-3.5-turbo")

# llm = Anthropic(model="claude-3-sonnet-20240229")


#LOCAL OLLAMA LLMs

llm = Ollama(model="mixtral",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)
# llm = Ollama(model="llama3:instruct",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)
# llm = Ollama(model="command-r:latest",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)

llm_sql = Ollama(model="mixtral",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)
# llm_sql = Ollama(model="dolphin-mixtral",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)
# llm_sql = Ollama(model="llama3:instruct",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)
# llm_sql = Ollama(model="command-r:latest",base_url="http://192.168.2.201:11434" ,request_timeout=300.0)




