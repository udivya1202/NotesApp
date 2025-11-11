import os
import pickle
import uuid
from datetime import datetime

import docx
import openai
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from fpdf import FPDF
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["VECTORSTORE_PATH"] = "vectorstore"
app.config["SESSIONS_PATH"] = "sessions"
app.config["ALLOWED_EXTENSIONS"] = {"pdf", "docx"}

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")


# Create necessary directories
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["VECTORSTORE_PATH"], exist_ok=True)
os.makedirs(app.config["SESSIONS_PATH"], exist_ok=True)
os.makedirs("generated_files", exist_ok=True)

# In-memory storage for conversation chains (key: session_id)
conversation_chains = {}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def get_session_key(user_id, session_id):
    """Create a unique key for user-session combination"""
    return f"{user_id}_{session_id}"


def get_session_path(user_id, session_id):
    """Get the file path for session metadata"""
    return os.path.join(
        app.config["SESSIONS_PATH"], f"{user_id}_{session_id}_session.pkl"
    )


def get_vectorstore_path(user_id, session_id):
    """Get the file path for session vectorstore"""
    return os.path.join(
        app.config["VECTORSTORE_PATH"], f"{user_id}_{session_id}_vectorstore.pkl"
    )


def load_session_metadata(user_id, session_id):
    """Load session metadata from disk"""
    session_path = get_session_path(user_id, session_id)
    if os.path.exists(session_path):
        with open(session_path, "rb") as f:
            return pickle.load(f)
    return None


def save_session_metadata(user_id, session_id, metadata):
    """Save session metadata to disk"""
    session_path = get_session_path(user_id, session_id)
    with open(session_path, "wb") as f:
        pickle.dump(metadata, f)


def load_vectorstore(user_id, session_id):
    vectorstore_path = get_vectorstore_path(user_id, session_id).replace(".pkl", "")
    if os.path.exists(vectorstore_path):
        return FAISS.load_local(
            vectorstore_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True
        )
    return None


def save_vectorstore(user_id, session_id, vectorstore):
    vectorstore_path = get_vectorstore_path(user_id, session_id)
    # Remove .pkl extension for save_local
    vectorstore_path = vectorstore_path.replace(".pkl", "")
    vectorstore.save_local(vectorstore_path)


def get_user_sessions(user_id):
    """Get all sessions for a user"""
    sessions = []
    sessions_dir = app.config["SESSIONS_PATH"]

    for filename in os.listdir(sessions_dir):
        if filename.startswith(f"{user_id}_") and filename.endswith("_session.pkl"):
            session_id = filename.replace(f"{user_id}_", "").replace("_session.pkl", "")
            metadata = load_session_metadata(user_id, session_id)
            if metadata:
                sessions.append(metadata)

    # Sort by last updated
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return sessions


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        pdf_reader = PdfReader(file_path)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""


def extract_text_from_file(file_path, file_type):
    """Extract text based on file type"""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    return ""


def get_text_chunks(text):
    """Split text into chunks for vector store"""
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def update_vectorstore(user_id, session_id, text):
    """Update or create vectorstore with new text"""
    text_chunks = get_text_chunks(text)
    embeddings = OpenAIEmbeddings()

    # Load existing vectorstore or create new one
    existing_vectorstore = load_vectorstore(user_id, session_id)

    if existing_vectorstore:
        # Add new texts to existing vectorstore
        existing_vectorstore.add_texts(text_chunks)
        vectorstore = existing_vectorstore
    else:
        # Create new vectorstore
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)

    # Save updated vectorstore
    save_vectorstore(user_id, session_id, vectorstore)
    return vectorstore


def get_conversation_chain(user_id, session_id):
    """Get or create conversation chain for a session"""
    session_key = get_session_key(user_id, session_id)

    if session_key in conversation_chains:
        return conversation_chains[session_key]

    # Load vectorstore
    vectorstore = load_vectorstore(user_id, session_id)
    if not vectorstore:
        return None

    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

    # Create a simple prompt template
    prompt = ChatPromptTemplate.from_template("""
    Answer the question based on the following context:
    
    Context: {context}
    
    Question: {input}
    
    Answer:""")

    # Create document chain
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Create retrieval chain
    retriever = vectorstore.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    conversation_chains[session_key] = retrieval_chain

    return retrieval_chain


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route("/sessions/create", methods=["POST"])
def create_session():
    """Create a new chat session for a user"""
    try:
        data = request.json
        user_id = data.get("user_id")
        session_name = data.get("session_name", "New Chat")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create session metadata
        session_metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0,
            "documents": [],
        }

        # Save session metadata
        save_session_metadata(user_id, session_id, session_metadata)

        return jsonify(
            {"message": "Session created successfully", "session": session_metadata}
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sessions/<user_id>", methods=["GET"])
def get_sessions(user_id):
    """Get all sessions for a user"""
    try:
        sessions = get_user_sessions(user_id)
        return jsonify(
            {"user_id": user_id, "sessions": sessions, "count": len(sessions)}
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sessions/<user_id>/<session_id>", methods=["GET"])
def get_session(user_id, session_id):
    """Get a specific session"""
    try:
        metadata = load_session_metadata(user_id, session_id)

        if not metadata:
            return jsonify({"error": "Session not found"}), 404

        return jsonify({"session": metadata}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sessions/<user_id>/<session_id>", methods=["PUT"])
def update_session(user_id, session_id):
    """Update session metadata (e.g., rename)"""
    try:
        data = request.json
        metadata = load_session_metadata(user_id, session_id)

        if not metadata:
            return jsonify({"error": "Session not found"}), 404

        # Update fields
        if "session_name" in data:
            metadata["session_name"] = data["session_name"]

        metadata["updated_at"] = datetime.now().isoformat()

        save_session_metadata(user_id, session_id, metadata)

        return jsonify(
            {"message": "Session updated successfully", "session": metadata}
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sessions/<user_id>/<session_id>", methods=["DELETE"])
def delete_session(user_id, session_id):
    """Delete a session and all associated data"""
    try:
        # Remove session metadata
        session_path = get_session_path(user_id, session_id)
        if os.path.exists(session_path):
            os.remove(session_path)

        # Remove vectorstore
        vectorstore_path = get_vectorstore_path(user_id, session_id)
        if os.path.exists(vectorstore_path):
            os.remove(vectorstore_path)

        # Remove from memory
        session_key = get_session_key(user_id, session_id)
        if session_key in conversation_chains:
            del conversation_chains[session_key]

        return jsonify({"message": "Session deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_documents():
    """Upload documents to a specific session"""
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files")
        user_id = request.form.get("user_id")
        session_id = request.form.get("session_id")

        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id are required"}), 400

        if not files:
            return jsonify({"error": "No files selected"}), 400

        # Load session metadata
        metadata = load_session_metadata(user_id, session_id)
        if not metadata:
            return jsonify({"error": "Session not found"}), 404

        uploaded_files = []
        all_text = ""

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{user_id}_{session_id}_{uuid.uuid4()}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                file.save(file_path)

                # Extract text based on file type
                file_type = filename.rsplit(".", 1)[1].lower()
                text = extract_text_from_file(file_path, file_type)
                all_text += text + "\n\n"

                doc_info = {
                    "filename": filename,
                    "saved_as": unique_filename,
                    "type": file_type,
                    "uploaded_at": datetime.now().isoformat(),
                }
                uploaded_files.append(doc_info)
                metadata["documents"].append(doc_info)

        if all_text.strip():
            # Update vectorstore with new documents
            update_vectorstore(user_id, session_id, all_text)

            # Update session metadata
            metadata["updated_at"] = datetime.now().isoformat()
            save_session_metadata(user_id, session_id, metadata)

            return jsonify(
                {
                    "message": "Documents uploaded successfully",
                    "files": uploaded_files,
                    "session_id": session_id,
                }
            ), 200
        else:
            return jsonify({"error": "No text could be extracted from files"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Chat with documents in a specific session"""
    try:
        data = request.json
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        question = data.get("question", "")

        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id are required"}), 400

        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Get or create conversation chain
        conversation_chain = get_conversation_chain(user_id, session_id)

        if not conversation_chain:
            return jsonify(
                {"error": "No documents uploaded yet. Please upload documents first."}
            ), 400

        # Get response using the new chain format
        response = conversation_chain.invoke({"input": question})
        answer = response["answer"]

        # Update session metadata
        metadata = load_session_metadata(user_id, session_id)
        if metadata:
            metadata["message_count"] = metadata.get("message_count", 0) + 1
            metadata["updated_at"] = datetime.now().isoformat()

            # Store chat history in metadata
            if "chat_history" not in metadata:
                metadata["chat_history"] = []

            metadata["chat_history"].append(
                {
                    "question": question,
                    "answer": answer,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            save_session_metadata(user_id, session_id, metadata)

        return jsonify({"answer": answer, "session_id": session_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat-history/<user_id>/<session_id>", methods=["GET"])
def get_chat_history(user_id, session_id):
    """Get chat history for a specific session"""
    try:
        metadata = load_session_metadata(user_id, session_id)

        if not metadata:
            return jsonify({"error": "Session not found"}), 404

        history = metadata.get("chat_history", [])

        return jsonify(
            {"user_id": user_id, "session_id": session_id, "history": history}
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate-notes", methods=["POST"])
def generate_notes():
    """Generate study notes from documents in a session"""
    try:
        data = request.json
        user_id = data.get("user_id")
        session_id = data.get("session_id")

        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id are required"}), 400

        # Load vectorstore to get document text
        vectorstore = load_vectorstore(user_id, session_id)

        if not vectorstore:
            return jsonify(
                {"error": "No documents uploaded yet. Please upload documents first."}
            ), 400

        # Get all documents from vectorstore
        docs = vectorstore.similarity_search("", k=100)
        text = "\n\n".join([doc.page_content for doc in docs])

        # Limit text length for API
        max_chars = 12000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        # Generate notes using OpenAI with new API
        prompt = (
            "You are a helpful assistant. Please convert the following text into clear, "
            "concise, and easy-to-understand notes that would be ideal for a student studying for a test. "
            "Focus on key concepts, important details, and summaries that aid in quick revision and understanding.\n\n"
            "Text:\n" + text
        )

        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful study assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
        )

        notes = response.choices[0].message.content.strip()

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Handle encoding issues
        notes_encoded = notes.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 10, notes_encoded)

        # Save PDF
        pdf_filename = f"notes_{user_id}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join("generated_files", pdf_filename)
        pdf.output(pdf_path)

        return jsonify(
            {
                "notes": notes,
                "pdf_filename": pdf_filename,
                "message": "Notes generated successfully",
                "session_id": session_id,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate-practice-test", methods=["POST"])
def generate_practice_test():
    """Generate practice test questions from documents in a session"""
    try:
        data = request.json
        user_id = data.get("user_id")
        session_id = data.get("session_id")

        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id are required"}), 400

        # Load vectorstore to get document text
        vectorstore = load_vectorstore(user_id, session_id)

        if not vectorstore:
            return jsonify(
                {"error": "No documents uploaded yet. Please upload documents first."}
            ), 400

        # Get all documents from vectorstore
        docs = vectorstore.similarity_search("", k=100)
        text = "\n\n".join([doc.page_content for doc in docs])

        # Limit text length for API
        max_chars = 12000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        # Generate questions using OpenAI with new API
        prompt = f"Create practice questions based on these notes: \n\n{text}"

        client = openai.OpenAI(api_key=openai.api_key)
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct", prompt=prompt, max_tokens=1000
        )

        questions = response.choices[0].text.strip()

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Handle encoding issues
        questions_encoded = questions.encode("latin-1", "replace").decode("latin-1")
        for line in questions_encoded.split("\n"):
            if line.strip():
                pdf.multi_cell(0, 10, line)

        # Save PDF
        pdf_filename = f"practice_test_{user_id}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join("generated_files", pdf_filename)
        pdf.output(pdf_path)

        return jsonify(
            {
                "questions": questions,
                "pdf_filename": pdf_filename,
                "message": "Practice test generated successfully",
                "session_id": session_id,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """Download generated PDF files"""
    try:
        file_path = os.path.join("generated_files", filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
