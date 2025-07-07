from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.response_synthesizers import TreeSummarize
from llama_index.core.query_pipeline import QueryPipeline,InputComponent
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
import os
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core import Settings,ChatPromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import (
    VectorStoreIndex,
    Settings
)
from llm import llm,parser
import json

PERSIST_DIR = "./storageDoauneCode"
if not os.path.exists(PERSIST_DIR):
    with open("coude_doaune_titles.json", 'r') as file:
        data = json.load(file)

        for index,item in enumerate(data):
            title = item.get('title', 'N/A')
            file = item.get('file', 'N/A')

            file_extractor = {".pdf": parser}
            reader = SimpleDirectoryReader(input_files=[f"./douane_pdfs/{file}"], file_extractor=file_extractor)
            documents = reader.load_data()
            for doc in documents:
                doc.metadata.update({'title':title})  
            Settings.context_window = 4096
            Settings.num_output = 256

    index = VectorStoreIndex.from_documents(documents, transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=20)], llm=llm)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

retriever = index.as_retriever(similarity_top_k=5)
reranker = CohereRerank()
summarizer = TreeSummarize(llm=llm)

chat_text_qa_msgs = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="Always answer the question, even if the context isn't helpful."
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=(
                    "Context below.\n"
                    "{context_str}\n"
                    "Given documents and context below, "
                    "answer the question: {query_str}\n"
                ),
            ),
        ]

        # Simplify and condense messages for refinement template
chat_refine_msgs = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="Always answer the question, even if the context isn't helpful."
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=(
                    "Refine the original answer with more context below.\n"
                    "{context_msg}\n"
                    "Given new context, refine the original answer: {query_str}. "
                    "If context isn't useful, output the original answer.\n"
                    "Original Answer: {existing_answer}"
                ),
            ),
        ] 
# define query pipeline
text_qa_template = ChatPromptTemplate(chat_text_qa_msgs)
refine_template = ChatPromptTemplate(chat_refine_msgs)
        # Query engine setup
engine = index.as_query_engine(
    text_qa_template=text_qa_template,
    refine_template=refine_template,
    llm=llm,    
    similarity_top_k=10,
)
# define query pipeline
# p = QueryPipeline(verbose=True)
# p.add_modules(
#     {
#         "input":InputComponent(),
#         # "prompt":prompt_tmpl,
#         "retriever": retriever,
#         "llm":llm,
#         "summarizer": summarizer,
#         "reranker": reranker,
#     }
# )


# p.add_link("input", "retriever")
# p.add_link("retriever", "reranker", dest_key="nodes")
# p.add_link("input", "reranker", dest_key="query_str")
# p.add_link("reranker", "summarizer", dest_key="nodes")
# p.add_link("input", "summarizer", dest_key="query_str")



