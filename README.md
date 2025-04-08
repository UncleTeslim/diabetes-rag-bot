# 🩺 DiabeticBot – Diabetes Question Answering Chat App (RAG-based)

DiabeticBot is a Retrieval-Augmented Generation (RAG) powered web application designed to answer natural language questions about **diabetes**. It leverages **LangChain**, **OpenAI's GPT-4** (or Gemini), and **Pinecone** vector store to retrieve accurate information from a curated PDF dataset of diabetes-related medical content (e.g. NIH or textbooks).

---

## 📌 Features

- ✅ Ask free-form questions like "Can a diabetic person have a baby?" or "What causes diabetes?"
- 🔍 Contextual answers based on your diabetes PDF knowledge base
- 🤖 Uses LLMs (GPT-4o / Gemini) with vector search (Pinecone)
- ⚙️ Streamlined Flask backend + HTML/JS frontend
- 🪶 Lightweight and minimal — perfect for hosting or demos

---

## 🧠 Tech Stack

| Layer        | Tech Used                |
|--------------|--------------------------|
| Frontend     | HTML, CSS, JavaScript (Fetch API) |
| Backend      | Python, Flask            |
| LLM & RAG    | LangChain, OpenAI |
| Embeddings   | OpenAI Embeddings        |
| Vector Store | Pinecone                 |
| Data Source  | PDF documents on diabetes (Textbook of diabetes, https://www.blackwellpublishing.com/content/textbookofdiabetes/downloads/chapters/allchapters.pdf) |
| Deployment   | Render / localhost       |

---


---

## 🛠️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/diabeticbot.git
cd diabeticbot
```


### 2. Create & Activate Conda/Virtual Environment

```bash
conda create -n diabeticbot python=3.10 -y
conda activate diabeticbot
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a .env file in the root directory:
```env
OPENAI_API_KEY=your_openai_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENV=your_pinecone_env
PINECONE_INDEX_NAME=your_index_name
```

### 5. Run the App
```bash
python app.py
```

## 🧪 How It Works

1. **PDF is loaded** and split into chunks using `PyPDFLoader`.
2. **Embeddings** are generated via OpenAI's embedding model.
3. The chunks are stored in **Pinecone** vector database with metadata.
4. When the user asks a question:
   - The app retrieves top relevant chunks from Pinecone using semantic search.
   - LangChain passes these chunks and the question to the LLM as context.
   - The LLM (OpenAI GPT-4 or Gemini) generates a context-aware response.
5. The answer is returned and shown in the web interface as coming from **DiabeticBot**.

---

## 📝 Example Questions

- What are the symptoms of diabetes?
- Can diabetes affect pregnancy?
- How do you manage type 2 diabetes naturally?
- What foods should a diabetic avoid?

---

## 📦 Sample Output

**Input:**  
can a diabetic person make baby?


**Output:**  
```makefile
**Output:**  
```
DiabeticBot: Yes, individuals with diabetes can have children. However, managing blood glucose levels before and during pregnancy is crucial to reduce risks for both the parent and the baby.



---

## ⚙️ Deployment (Optional)

You can deploy the app using:

- **Render**: Docker-free, simple Python app deployment
- **Railway** or **Replit**: Good for fast previews and prototyping
- **Azure App Services / GCP App Engine**: Ideal for enterprise environments

### Deployment Checklist:

- Store all API keys in environment variables or secrets manager
- Replace localhost URLs with environment-aware ones
- Remove Flask debug mode for production
- Consider enabling HTTPS and CORS

---

## ✅ Future Improvements

- [ ] Add user authentication with session/token support
- [ ] Store question history and allow revisiting previous queries
- [ ] Switch to local vector DB (e.g., FAISS or ChromaDB) for full open-source setup
- [ ] Add audio input/output (voice mode)
- [ ] Progressive Web App (PWA) version for mobile access

---


---

## 📄 License

This project is licensed under the **MIT License**. See `LICENSE` file for details.

---
