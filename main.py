import os, re
import fitz
import numpy as np
import pandas as pd
from PIL import Image
import psycopg2
import pytesseract
from db_helper import *
from pdf2image import convert_from_path
pytesseract.pytesseract.tesseract_cmd =r"C:\Users\krishna_shinde\AppData\Local\Programs\Tesseract-OCR\tesseract"


class DictDataStore(dict):
    # __init__ function
    def __init__(self):
        self = dict()
         
    # Function to add key:value
    def add(self, key, value):
        self[key] = value 


class ExtractData():

    def __init__(self):
        self.regex = r"[!\"#\$%&\'\(\)\*\+,-\./:;<=>\?@\[\\\]\^_`{\|}~]"
        self.poppler_path=r"poppler-23.07.0\Library\bin"
        self.pdf_path = "coding_standards.pdf"
        #Create empty list to store texts information
        self.text_data = ''
        #Create empty list to store images information
        self.images_list = []
        self.image_data = []
        #Define path for saved images
        self.images_path = 'images/'

    def extract_text_from_pdf(self, pdf_path, dict):
        self.pdf_path = pdf_path
        # Convert PDF to image
        pages = convert_from_path(self.pdf_path, poppler_path=self.poppler_path)
        # Extract text from each page using Tesseract OCR
        for page_number, page_data in enumerate(pages):
            text = pytesseract.image_to_string(Image.fromarray(np.array(page_data)))
            # .encode("utf-8")
            text = str(text).replace("\n", " ")
            text = re.sub(self.regex, "", text, 0, re.MULTILINE)
            self.text_data += f"Page # {page_number} : {text}" + '\n'

            dict.add(page_number + 1, text)
        
        # Return the text data
        return self.text_data
    
    def extract_image_from_pdf(self, pdf_path):
        self.pdf_path = pdf_path
        # open file
        pdfFile = fitz.open(self.pdf_path)
        page_nums = len(pdfFile)        

        for page_index in range(page_nums): 
            # get the page itself
            page = pdfFile[page_index]
            self.images_list = page.get_images()

            # printing number of images found in this page
            if len(self.images_list)>0:
                for j, img in enumerate(self.images_list, start=1):
                    xref = img[0]
                    #Extract image
                    base_image = pdfFile.extract_image(xref)
                    #Store image bytes
                    image_bytes = base_image['image']
                    #Store image extension
                    image_ext = base_image['ext']
                    #Generate image file name
                    image_name = str(str(page_index+1)+" "+str(j)) + '.' + image_ext
                    #Save image
                    with open(os.path.join(self.images_path, image_name) , 'wb') as image_file:
                        image_file.write(image_bytes)
                        image_file.close()
                    
                    self.image_data.append((image_bytes, page_index+1))
                print(
                    f"[+] Found a total of {len(self.images_list)} images in page {page_index+1}")
            else:
                print("[!] No images found on page", page_index+1)

        return self.image_data

if __name__ == "__main__":

    File_name = 'coding_standards.pdf'
    File_name.lower()
    
    # Create DataStore.
    Extracted_text = DictDataStore()

    text_data = ExtractData().extract_text_from_pdf(File_name, Extracted_text)
    # print(text_data)

    image_data = ExtractData().extract_image_from_pdf(File_name)
    # print(image_data)

    texts_df = pd.DataFrame(list(Extracted_text.items()),columns = ['page_num','txts'])
    texts_query = "INSERT INTO texts(page_num, txts) VALUES %s"
    
    # images_df = pd.DataFrame(list(Extracted_images.items()),columns = ['fk_page_num','images_bb'])
    images_df = pd.DataFrame(image_data, columns =['fk_page_num','images_bb'])
    images_query = "INSERT INTO images(images_bb, fk_page_num) VALUES %s"
    
    db_connect = DBHelper(File_name[:-4])
    conn_info = db_connect.load_connection_info("db.ini")
    db_connect.create_db(conn_info)
    conn = psycopg2.connect(**conn_info)
    
    db_connect.create_table_schema(conn, conn.cursor())
    db_connect.insert_data(texts_query, conn, conn.cursor(), texts_df, 100)
    db_connect.insert_data(images_query, conn, conn.cursor(), images_df, 100)


    # Retrieve 1 image from database
    # blob_image = db_connect.read_blob(conn, conn.cursor())

    # Close all connections to the database
    # conn.close()
    # conn.cursor().close()

