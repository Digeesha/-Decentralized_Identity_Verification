import os
import time
import json
import hashlib
import sqlite3
import re
from web3 import Web3
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, session
import easyocr

# Load environment variables
load_dotenv()
GANACHE_URL = os.getenv("GANACHE_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FROM_ADDRESS = os.getenv("FROM_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID"))

# Initialize web3 and EasyOCR
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
ocr_reader = easyocr.Reader(['en'])

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Ensure folders and DB exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

conn = sqlite3.connect('document_verification.db')
c = conn.cursor()
c.execute(''' 
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_name TEXT,
        document_hash TEXT,
        txn_hash TEXT,
        timestamp TEXT
    )
''')
conn.commit()
conn.close()

# --- Utility Functions ---
def normalize_json(data):
    return {k.lower().replace(" ", "_").replace("-", "_").strip(): str(v).lower().strip() for k, v in data.items()}

def normalize_data_for_hashing(data):
    if isinstance(data, dict):
        return {k.lower().strip(): normalize_data_for_hashing(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return [normalize_data_for_hashing(item) for item in data]
    elif isinstance(data, str):
        return data.strip()
    return data

def extract_hashable_signature(data):
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, list):
                cleaned[k] = sorted([json.dumps(normalize_json(item), sort_keys=True) for item in v if isinstance(item, dict)])
            else:
                cleaned[k] = str(v).strip().lower()
        return dict(sorted(cleaned.items()))
    return data

def extract_text_from_image(image_path):
    result = ocr_reader.readtext(image_path, detail=0)
    return " ".join(result).lower()

def store_in_db(participant_name, document_hash, txn_hash):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('document_verification.db')
    c = conn.cursor()
    c.execute(''' 
        INSERT INTO documents (participant_name, document_hash, txn_hash, timestamp) 
        VALUES (?, ?, ?, ?)
    ''', (participant_name, document_hash, txn_hash, timestamp))
    conn.commit()
    conn.close()

def store_hash_on_blockchain(document_hash):
    account = web3.eth.account.from_key(PRIVATE_KEY)
    nonce = web3.eth.get_transaction_count(account.address)
    transaction = {
        'to': FROM_ADDRESS,
        'value': web3.to_wei(0, 'ether'),
        'gas': 2000000,
        'gasPrice': web3.to_wei('50', 'gwei'),
        'nonce': nonce,
        'chainId': CHAIN_ID,
        'data': web3.to_bytes(hexstr=document_hash)
    }
    signed_txn = web3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Document hash stored in blockchain with txn hash: {web3.to_hex(txn_hash)}")
    return txn_hash

# --- Flask Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/verify')
def verify():
    return render_template('verify.html')

@app.route('/upload_details')
def upload_details():
    return render_template('upload.html')

@app.route('/upload_data', methods=['POST'])
def upload_data():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected file"}), 400

    save = os.path.join('uploads', image.filename)
    image.save(save)

    doc_type = request.form.get("doc_type", "").lower()
    text_data = extract_text_from_image(save)
    print(f"Extracted Text: {text_data}")

    # --- Regex-Based Extraction ---
    if doc_type == "student_id":
        if "student" not in text_data or "id" not in text_data:
            return jsonify({"error": "Invalid student ID document."}), 400
        name_match = re.search(r'name[:\s]+([a-z\s]+)', text_data)
        id_match = re.search(r'student[\s_]*id[:\s]+(\d+)', text_data)
        grade_match = re.search(r'grade[\s_-]*year[:\s]+([\d/]+)', text_data)
        issued_match = re.search(r'issued[\s_-]*on[:\s]+([a-z]+\s\d{1,2},?\s*\d{4})', text_data)

        result_data = {
            "full_name": name_match.group(1).strip().title() if name_match else "Unknown",
            "student_id": id_match.group(1).strip() if id_match else "Unknown",
            "grade_year": grade_match.group(1).strip() if grade_match else "Unknown",
            "issued_on": issued_match.group(1).strip().title() if issued_match else "Unknown"
        }

    elif doc_type == "certificate":
        if "certificate" not in text_data:
            return jsonify({"error": "Invalid certificate document."}), 400
        name_match = re.search(r'name[:\s]+([a-z\s]+)', text_data)
        title_match = re.search(r'certificate[\s-]*of[:\s]*([a-z\s]+)', text_data)

        result_data = {
            "full_name": name_match.group(1).strip().title() if name_match else "Unknown",
            "certificate_title": title_match.group(1).strip().title() if title_match else "Unknown"
        }

    elif doc_type == "internship":
        if "internship" not in text_data and "completion" not in text_data:
            return jsonify({"error": "Invalid internship document."}), 400
        name_match = re.search(r'name[:\s]+([a-z\s]+)', text_data)
        company_match = re.search(r'at[:\s]+([a-z\s]+)', text_data)
        role_match = re.search(r'role[:\s]+([a-z\s]+)', text_data)
        duration_match = re.search(r'duration[:\s]+([\w\s]+)', text_data)

        result_data = {
            "full_name": name_match.group(1).strip().title() if name_match else "Unknown",
            "company_name": company_match.group(1).strip().title() if company_match else "Unknown",
            "role": role_match.group(1).strip().title() if role_match else "Unknown",
            "duration": duration_match.group(1).strip().title() if duration_match else "Unknown"
        }

    else:
        return jsonify({"error": "Invalid document type selected."}), 400

    name = result_data.get("full_name", "unknown")
    normalized = normalize_data_for_hashing(result_data)
    signature = extract_hashable_signature(normalized)
    json_string = json.dumps(signature, sort_keys=True)
    document_hash = hashlib.sha256(json_string.encode()).hexdigest()

    print(f"Calculated Document Hash: {document_hash}")
    is_verified = verify_data(document_hash)

    session['dictionary'] = result_data
    session['verify_result'] = is_verified
    session['document_hash'] = document_hash

    if is_verified == "❌ Verification failed! Doesn't Exist.":
        txn_hash = store_hash_on_blockchain(document_hash)
        store_in_db(name.lower(), document_hash, web3.to_hex(txn_hash))

    return jsonify({"success": True, "message": "Verification complete.", "redirect": "/result"})

def verify_data(document_hash):
    conn = sqlite3.connect('document_verification.db')
    c = conn.cursor()
    c.execute('SELECT document_hash FROM documents WHERE document_hash = ?', (document_hash,))
    result = c.fetchone()
    conn.close()

    if result:
        print(f"Document hash found in DB: {document_hash}")
        return "✅ Document has been verified on blockchain."
    else:
        print("Hash not found in database.")
        return "❌ Verification failed! Doesn't Exist."

@app.route('/result')
def result():
    verify_result = session.get('verify_result', 'No result available.')
    document_hash = session.get('document_hash', 'No hash available.')
    return render_template('result.html', verify_result=verify_result, document_hash=document_hash)

if __name__ == '__main__':
    app.run(debug=True)
