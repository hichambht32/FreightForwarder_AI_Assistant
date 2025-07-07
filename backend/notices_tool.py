
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
    ChatPromptTemplate,
)
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole
import json
from llama_index.core.schema import MetadataMode
from llm import llm


#circulaire qu'on troune en recherchant produit chimique uniquement 
folder1="chemist_circ"

#tous les circulaires
folder2="pdfs"




try:
    storage_context = StorageContext.from_defaults(
        persist_dir=f"./circulaire_prod_chimie_store"
    )
    index = load_index_from_storage(storage_context)

except:
    with open(f"{folder1}.json", 'r') as file:
        data = json.load(file)
        total_docs = [] 
        for item in data:
            circular_number = item.get('circular_number', 'N/A')
            date = item.get('date', 'N/A')
            objet = item.get('objet', 'N/A')
            reference = item.get('reference', 'N/A')
            file_name = item.get('file', 'N/A')

            # Load data
            docs = SimpleDirectoryReader(
                input_files=[f"./chemist_circ/{file_name}.pdf"]
            ).load_data()

            data ={"circulaire_date":date,'objet':objet,'reference':reference,'circulair_number':circular_number} 
            for doc in docs:
                doc.metadata.update(data)  
                # print(doc.get_content(metadata_mode=MetadataMode.LLM))
            
            # Set context window and number of output tokens
            Settings.context_window = 4096
            Settings.num_output = 256
            total_docs.extend(docs)  
    index = VectorStoreIndex.from_documents(total_docs, transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=20)], llm=llm)
    # Persist index
    index.storage_context.persist(persist_dir=f"./circulaire_prod_chimie_store")


# Define chat templates
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

text_qa_template = ChatPromptTemplate(chat_text_qa_msgs)
refine_template = ChatPromptTemplate(chat_refine_msgs)
# Query engine setup
circ_engine = index.as_query_engine(
    text_qa_template=text_qa_template,
    refine_template=refine_template,
    llm=llm,
    similarity_top_k=3,
)

# Tool definition
# tool = QueryEngineTool(
#     query_engine=engine,
#     metadata=ToolMetadata(
#         object =f"Circulaires",
#         description=(
#             "un query engine sur les circulaires douaniere ."
#         ),
#     ),
# )     


