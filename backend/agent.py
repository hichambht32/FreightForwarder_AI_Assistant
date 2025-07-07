from uuid import uuid4
from flask import Flask, request, jsonify
from llm import llm
from llama_index.core.tools import FunctionTool,QueryEngineTool
from llama_index.core.agent import ReActAgent
from doc_required_tool import DocsRequired
from Taxes_tool import ImportDuties
from sql_query import NL2SQLfn
from codification_tool import PositionTarifaire
from ReportTool import fetch_data_and_add_to_pdf
from prompt import new_tmpl
from code_douane_tool import engine
from recommendations_tool import getSimilarNames
from notices_tool import circ_engine
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

NL2SQLtool = FunctionTool.from_defaults(
    fn=NL2SQLfn,
    description="IN FRENCH.Use this tool to query a database containing data tables for Importers, Exporters, Annual Import, Annual Export, Suppliers, and Clients using natural language in French. The tool converts the natural language input into an SQL command to search the database, providing quick and accurate data retrieval without requiring knowledge of SQL."
)

DocsRequiredtool = FunctionTool.from_defaults(
    fn=DocsRequired,
    description="This tool is designed to identify the required documents and autorisations for importing a specific product into morroco. Users can input their query in natural language (French), and the tool will convert the input into an SQL command to search through a database of required documents for various products. When to use: Use this tool when you want to find out the documents name and number and their issuer required."
)

taxesTool = FunctionTool.from_defaults(
    fn=ImportDuties,
    description="This tool is designed to provide detailed information on import duties (DI), value-added tax (TVA), and specific product tax (TPI) for a given product. Users can input their queries in natural language (French), and the tool will convert the input into an SQL command to search through a database of relevant tax data. When to use: Use this tool when you want to know the DI, TVA, and TPI for a specific product."
)

# positiontarifairetool = FunctionTool.from_defaults(
#     fn=PositionTarifaire,
#     description="This tool is designed to provide information on Harmonized System (HS) tariff codes, including codification, name, and category. Users can input their queries in natural language, and the tool will convert the input into an SQL command to search through a database of tariff positions. This tool is primarily for querying a database to retrieve HS codes or the chapters they belong to. When to use: Use this tool when you need to query a database for information on HS tariff codes, including codification, name, and category, or to find the chapters these codes belong to."
# )

codeDouane_query_engine = QueryEngineTool.from_defaults(
            query_engine=engine,
            name="codeDouane",
            description=(
                    "This tool serves as a query engine for accessing all laws and regulations related to customs in Morocco, including all important articles dating back to the first Dahir in 1977. Users can query in natural language to find specific customs laws and regulations.When to use: Use this tool when you need information on Moroccan customs laws and regulations."
                )
        )

identify_product = FunctionTool.from_defaults(
    fn=getSimilarNames,
    description="IN FRENCH always use it first, this tool takes in the product name as an input and returns a list of any products name that is similar using Levenshtein method and their HS code.if distance = 0 its the right product otherwise return the list to the user so he can choose."
)

circulars_query_engine = QueryEngineTool.from_defaults(
            query_engine=circ_engine,
            name="circulaire",
            description=(
                    "un query engine sur les circulaires douaniere ."
                )
        )

ReportingTool = FunctionTool.from_defaults(
    fn=fetch_data_and_add_to_pdf,
    description="This tool fetches data from a database via the HS code, adds it to a PDF report, and converts the file into a Dropbox link for easy sharing. Use this tool to quickly generate a PDF report and receive a shareable Dropbox link. Don't use any other tool with it except from the getSimilarNames tool."
)


agent = ReActAgent.from_tools(
        tools=[NL2SQLtool,taxesTool,DocsRequiredtool,identify_product,codeDouane_query_engine,ReportingTool], 
        llm=llm, 
        verbose=True,
        max_iterations=20,
        )

agent.update_prompts(
    {"agent_worker:system_prompt": new_tmpl}
)

@app.route('/query', methods=['POST'])
def query_endpoint():
    data = request.json
    user_input = data.get('user_input', '') 
    message_id = data.get('message_id') or str(uuid4()) # Assuming message_id is provided in the request

    if not user_input:
        return jsonify({'error': 'Please provide a user input'}), 400

    try:
        # Assuming agent.chat returns a string or a serializable object
        print(user_input)
        response = agent.chat(user_input)
   
        # Modify the response as needed to ensure JSON serializability
        json_response = {
            'messageId': message_id,
            'responseText': str(response)}  # assuming response is a string
        return jsonify(json_response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error':str(e)}),500


if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'  # Ensure Flask runs in development mode
    app.run(debug=True, host='192.168.2.134', port=5000, use_reloader=True)

