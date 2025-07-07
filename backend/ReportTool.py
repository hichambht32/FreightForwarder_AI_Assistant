
from fpdf import FPDF
from sqlalchemy import MetaData, Table, create_engine, func, select
import logging
# from google.cloud import storage
import os
from datetime import datetime
import dropbox

DROPBOX_ACCESS_TOKEN = 'USE YOUR DROPBOX TOKEN'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Replace 'your_database_connection_string' with your actual connection string
database_connection_string = 'mysql://aiuser:topnegoce@192.168.2.134/Adildb'
engine = create_engine(database_connection_string)
# Create a MetaData object
metadata = MetaData()
# Reflect the existing tables using the engine
metadata.reflect(bind=engine)
# Get all table names
included_tables = metadata.tables.keys()
connection = engine.connect()

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Top Negoce Report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# Initialize PDF
pdf = PDF()
pdf.add_page()
tables_to_process = [table_name for table_name in included_tables if not table_name.endswith('_info')]
# print(tables_to_process)

def codification_bullets(code):
    codification_table = Table('codification', metadata, autoload=True, autoload_with=engine)
    query = codification_table.select().where(codification_table.c.code == code)
    codification_data = connection.execute(query).fetchall()
    
    # Add codification data to the PDF in bullet format
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Codification Data', ln=True)
    pdf.set_font('Arial', '', 10)

    for row in codification_data:
        for col in codification_table.columns:
            col_name = col.name
            # Exclude 'id' column and its value
            if col_name == 'id':
                continue
            col_index = codification_table.columns.keys().index(col_name)
            col_value = row[col_index]
            # Change column names if needed
            if col_name == 'chapter_number':
                col_name = 'Chapter'
            elif col_name == 'chapter_title':
                col_name = 'Chapter Title'
            elif col_name == 'name':
                col_name = 'Nomenclature'
            elif col_name == 'category':
                col_name = 'Category'

            # Add each column with bullet formatting
            pdf.cell(0, 10, f'- {col_name} :', ln=True)
            pdf.set_x(pdf.get_x() + 10)  # Indent for the bullet point
            
            # Check if the column value is a string before trying to replace text
            if isinstance(col_value, str):
                # Use MultiCell to allow text wrapping within the cell
                pdf.multi_cell(0, 10, col_value.replace('\n', ''), align='L')
            else:
                pdf.multi_cell(0, 10, str(col_value), align='L')  # Convert integer to string
            
            pdf.set_x(pdf.l_margin)  # Reset X position for the next iteration

def print_importers_as_bullets(code, table_name):
    # Fetch data from the "importers" table
    importers_table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    # print("importers table: ",table_name)
    query = importers_table.select().where(importers_table.c.code == code)
    importers_data = connection.execute(query).fetchall()

    # Add importers data to the PDF in bullet format
    pdf.set_font('Arial', 'B', 12)
    if table_name == 'importers':
        pdf.cell(0, 10, 'Importers Names', ln=True)
    elif table_name == "exporters":
        pdf.cell(0, 10, 'Exporters Names', ln=True)
    pdf.set_font('Arial', '', 10)

    for row in importers_data:
        for col in importers_table.columns:
            col_name = col.name
            if col_name in ['id', 'code']:
                continue
            col_index = importers_table.columns.keys().index(col_name)
            col_value = row[col_index]
            pdf.cell(0, 10, f'- {col_value}', ln=True)

def upload_pdf_to_dropbox(pdf_path, access_token):
    try:
        dbx = dropbox.Dropbox(access_token)

        with open(pdf_path, 'rb') as f:
            dbx.files_upload(f.read(), '/' + os.path.basename(pdf_path), mute=True)

        shared_link_metadata = dbx.sharing_create_shared_link_with_settings('/' + os.path.basename(pdf_path))
        return shared_link_metadata.url.replace('?dl=0', '?dl=1')  # Direct download link
    except Exception as e:
        logger.error(f"Failed to upload PDF to Dropbox: {e}")
        return None

def fetch_data_and_add_to_pdf(code):
    """
    A tool used to fetch data from the database and add it to the PDF reporter and return a DropBox link to it.
    """
    # Dictionary to map original table names to desired names for printing
    table_name_mapping = {
        'accord_convention': 'Agreement and Convention',
        'annual_export': 'Annual Export',
        'annual_import': 'Annual Import',
        'import_duty': 'Import Duty',
        'clients': 'Clients',
        'document_required': 'Document Required',
        'exporters': 'Exporters',
        'importers': 'Importers',
        'fournisseurs': 'Suppliers'
    }

    # Dictionary to map original column names to desired column names
    column_name_mapping = {
        'accord_convention': {'country': 'Country', 'di_percentage': 'DI', 'tpi_percentage': 'TPI', 'agreement': 'Agreement Type'},
        'annual_export': {'year': 'Year', 'weight': 'Weight (kg)', 'value': 'Value (Dh)'},
        'annual_import': {'year': 'Year', 'weight': 'Weight (kg)', 'value': 'Value (Dh)'},
        'clients': {'country': 'Country', 'weight': 'Weight (Kg)', 'value': 'Value (Dh)'},
        'document_required': {'document_number': 'Document Number', 'document_name': 'Document Name', 'libelle_d_extrait': "Excerpt's Label"},
        'exporters': {'name': 'Exporters Name'},
        'importers': {'name': 'Importers Name'},
        'fournisseurs': {'country': 'Country', 'value': 'Value (Dh)', 'weight': 'Weight (Kg)'}
    }
    
    pdf.set_font('Arial', 'B', 12)  # Set font for table headers
    
    # Process 'codification' table first if present
    if 'codification' in tables_to_process:
        tables_to_process.remove('codification')
        tables_to_process.insert(0, 'codification')

    for table_name in tables_to_process:
        # print(f"Processing table: {table_name}")
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        columns = table.columns.keys()
        # print(columns)
        
        if table_name == 'codification':
            codification_bullets(code)
        elif table_name == 'importers':
            print_importers_as_bullets(code, table_name)
        elif table_name == 'exporters':
            print_importers_as_bullets(code, table_name)
        else:
            print_table_name = table_name_mapping.get(table_name, table_name)

            # Add title with the desired table name
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'{print_table_name}', ln=True)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 10, '', ln=True)

            # Calculate total width of the table
            total_width = sum([40 for col_name in columns if col_name not in ['id', 'code']])
            # Calculate left padding to center the table
            left_padding = (pdf.w - total_width) / 2
            pdf.set_x(left_padding)  # Set the left padding

            for col_name in columns:
                if col_name in column_name_mapping.get(table_name, {}):
                    col_name = column_name_mapping[table_name][col_name]
                if col_name not in ['id', 'code']:
                    col_width = 40
                    pdf.cell(col_width, 10, col_name, 1, 0, 'C')
            pdf.ln()

            # Fetch data associated with the specified codification
            query = table.select().where(table.c.code == code)
            rows = connection.execute(query).fetchall()

            # Reflect the tables
            annual_export_table = Table('annual_export', metadata, autoload=True, autoload_with=engine)
            annual_import_table = Table('annual_import', metadata, autoload=True, autoload_with=engine)

            # Print data rows
            pdf.set_font('Arial', '', 10)
            for row in rows:
                pdf.set_x(left_padding)  # Set the left padding
                for i, col in enumerate(row):
                    if table.columns[i].name not in ['id', 'code']:
                        col_width = 40
                        texttest = str(col)
                        # Encode the text to 'latin-1' and ignore non-Latin-1 characters
                        text = texttest.encode('latin-1', 'ignore').decode('latin-1')
                        # Check if text exceeds cell width
                        if pdf.get_string_width(text) > col_width:
                            # Calculate reduction factor to fit text within cell width
                            reduction_factor = col_width / pdf.get_string_width(text)
                            # Adjust font size
                            pdf.set_font_size(10 * reduction_factor)
                        pdf.cell(col_width, 10, text, 1, 0, 'C')
                        # Reset font size to default
                        pdf.set_font_size(10)
                pdf.ln()
        pdf.ln()

    # Close the database connection
    engine.dispose()
    logger.info("PDF generated successfully")

    # Generate a unique timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    pdf_path = f'Douane_Report_of_{code}_{timestamp}.pdf'
    pdf.output(pdf_path)

    # Upload the PDF to Google Cloud Storage and get the public URL
    public_url = upload_pdf_to_dropbox(pdf_path, DROPBOX_ACCESS_TOKEN)
    
    if public_url:
        logger.info(f"PDF successfully uploaded. Access it here: {public_url}")
        return public_url
    else:
        logger.error("Failed to upload PDF to DBX.")
        return "Error: Could not generate the report link."


# fetch_data_and_add_to_pdf(2915700020)
