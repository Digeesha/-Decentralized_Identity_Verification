# Decentralized Identity Verification

A document verification system leveraging AI (EasyOCR + Gemini API) and blockchain (Web3 + Ganache) for tamper-proof proof of identity.

---

## 🔍 Features

- **AI-powered OCR**  
  Extract text from uploaded document images using EasyOCR and Google’s Gemini API.

- **Blockchain Anchoring**  
  Compute a SHA-256 hash of each document and store it on a local Ganache blockchain via a simple Solidity smart contract (`IdentityStorage.sol`) and Web3.

- **Web Interface**  
  Flask backend (`app.py`) serves an upload page for verification and displays on-chain transaction details.

- **Privacy-First**  
  Only cryptographic hashes are stored on-chain. No raw personal data is ever committed to the blockchain.

- **SQLite Logging**  
  Records each verification attempt—user name, document hash, transaction hash, and timestamp—in `document_verification.db`.

---

## 🚀 Prerequisites

- **Python 3.8+**  
- **Node.js 14+**, **npm** & **Truffle** (for compiling & deploying contracts)  
- **Ganache CLI or GUI** running on your machine  
- **Google Cloud credentials** with access to the Generative AI API (Gemini)  
- **Git** & a **GitHub** account

---

## ⚙️ Setup

1. **Clone & enter**  
   ```bash
   git clone https://github.com/Digeesha/-Decentralized_Identity_Verification.git
   cd -Decentralized_Identity_Verification
**
Create & activate Python venv**

python3 -m venv venv
source venv/bin/activate      # macOS/Linux
**Install Python dependencies**
pip install -r backend/requirements.txt
pip install easyocr opencv-python-headless

**Configure environment variables**
Copy the example file and edit it:
cp backend/.env.
example backend/.env
**Then open backend/.env and fill in:**
GANACHE_URL=http://127.0.0.1:7545
PRIVATE_KEY=<YOUR_GANACHE_ACCOUNT_PRIVATE_KEY>
FROM_ADDRESS=<YOUR_GANACHE_ACCOUNT_ADDRESS>
CHAIN_ID=1337
GOOGLE_API_KEY=<YOUR_GOOGLE_CLOUD_API_KEY>
**Deploy the smart contract**
npm install -g truffle          # if not already installed
cd backend
truffle compile
truffle migrate --reset --network development
cd ..


Running the App
Start Ganache on port 7545 (default).

Run the Flask server
cd backend
source ../venv/bin/activate     # if not already active
python app.py

Open your browser at http://127.0.0.1:5000
Upload a document image to verify.
View on-chain hash comparison, transaction hash, and local log.


