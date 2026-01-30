import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
import os
from ..config import EXCEL_PATH



def load_and_index_exercises():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Exercise data file not found at path: {EXCEL_PATH}")
    
    print(f"Loading exercise data from {EXCEL_PATH}...")
    
    df = pd.read_csv(EXCEL_PATH)
    
    documents = []
    for idx, row in df.iterrows():
        text = f"""
Exercise: {row.get('name', 'Unknown')}
Sport Category: {row.get('sport_category', '')}
Movement Pattern: {row.get('movement_pattern', '')}
Primary Muscles: {row.get('primary_muscles', '')}
Secondary Muscles: {row.get('secondary_muscles', '')}
CNS Load: {row.get('cns_load', '')}
Skill Level: {row.get('skill_level', '')}
Injury Risk: {row.get('injury_risk', '')}
Equipment: {row.get('equipment', '')}
Description: {row.get('description', '')}
"""
        documents.append(
            Document(
                page_content=text.strip(),
                metadata={"exercise_name": row.get('name', 'Unknown'), "row_id": idx}
            )
        )
        
    text_splitter = CharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    split_docs = text_splitter.split_documents(documents)
    
    embeddings = HuggingFaceEmbeddings(
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        collection_name="iron_ready_exercises",
        persist_directory="./chroma_db_exercise"
    )
    
    print(f"Successfully indexed {len(documents)} exercises into Chroma DB!")
    return vectorstore

if __name__ == "__main__":
    load_and_index_exercises()