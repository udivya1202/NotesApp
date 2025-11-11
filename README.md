# StudyBuddy - AI-Powered Document Q&A System

A Flask-based RAG (Retrieval-Augmented Generation) application that transforms your study materials into an interactive learning assistant. Upload lecture notes, textbooks, or any documents, and chat with them using natural language to get instant answers, generate study notes, and create practice tests.

## What It Does

**Document Management**
- Upload PDF and DOCX files to personalized study sessions
- Each user can create multiple sessions for different subjects or topics
- Automatically extracts and processes text from all uploaded documents
- Persistent storage - your documents and conversations are saved even after closing the app

**Intelligent Q&A**
- Ask questions about your documents in plain English
- Get accurate, context-aware answers powered by OpenAI's GPT-3.5
- Uses semantic search to find the most relevant information from your materials
- Maintains conversation history for each session

**Study Tools**
- **Generate Notes**: Automatically creates concise, organized study notes from all your documents
- **Practice Tests**: Generates practice questions based on your materials to help you prepare for exams
- Both tools export to PDF for easy printing or sharing

**Multi-User Support**
- Each user has their own isolated workspace
- Sessions are user-specific and independently managed
- No data mixing between different users/sessions

## How It Works

The application uses a RAG (Retrieval-Augmented Generation) architecture:

1. **Document Processing**: When you upload files, the text is extracted and split into smaller chunks
2. **Vectorization**: Each chunk is converted into a vector embedding using OpenAI's embedding model
3. **Storage**: These embeddings are stored in a FAISS vector database for lightning-fast similarity search
4. **Query Processing**: When you ask a question, it's converted to an embedding and matched against your documents
5. **Answer Generation**: The most relevant chunks are sent to GPT-3.5 along with your question to generate accurate, contextual answers

## Technical Stack

- **Backend Framework**: Flask with CORS support for web/mobile clients
- **AI/ML**: LangChain for RAG orchestration, OpenAI for embeddings and chat completions
- **Vector Database**: FAISS for efficient similarity search
- **Document Processing**: PyPDF2 for PDFs, python-docx for Word documents
- **PDF Generation**: FPDF for creating study materials
- **Storage**: File-based persistence using pickle for vector stores and session metadata

## Architecture

```
User → Flask API → Session Manager
                 ↓
         Document Processor → Text Chunks
                 ↓
         Vector Embeddings → FAISS Store
                 ↓
    User Question → Retriever → Relevant Chunks → GPT-3.5 → Answer
```

## Use Cases

- **Students**: Study for exams by chatting with lecture notes and textbooks
- **Researchers**: Quickly find information across multiple research papers
- **Professionals**: Get instant answers from company documentation or training materials
- **Learners**: Create personalized study guides from any learning materials

## Key Features

✨ **Session-Based Organization** - Keep different subjects separate with independent chat sessions

🔍 **Semantic Search** - Find information based on meaning, not just keywords

💾 **Persistent Storage** - All your data is saved and available across sessions

📝 **Automatic Summarization** - Convert lengthy documents into digestible study notes

❓ **Practice Question Generation** - Test your knowledge with AI-generated questions

🔒 **User Isolation** - Your data stays private and separate from other users

📄 **PDF Export** - Download your generated notes and practice tests

## API Design

RESTful API with endpoints for:
- Session management (create, read, update, delete)
- Document upload and processing
- Interactive chat with documents
- Chat history retrieval
- Study material generation

Each endpoint follows standard HTTP conventions with proper status codes and JSON responses.
