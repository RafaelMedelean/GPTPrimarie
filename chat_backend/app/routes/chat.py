from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uuid
from typing import List
from datetime import datetime
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI
import uvicorn

# Conversation endpoints models, authentication, and database operations
from ..models.models import (
    User,
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ChatRequest,
    ChatResponse,
    FeedbackRequest
)
from ..core.auth import get_current_active_user
from ..db.database import (
    create_conversation,
    get_conversation,
    get_user_conversations,
    update_conversation,
    delete_conversation,
    add_messages_to_conversation,
    update_message_feedback
)

# Load environment variables from .env file
load_dotenv()

# Retrieve Azure OpenAI credentials from environment variables
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

# Create the FastAPI app and configure CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

####################################
# Response Generation Functionality #
####################################

TOP_K = 5
device_emb = "cuda:1" if torch.cuda.is_available() else "cpu"

# Define a singleton for the SentenceTransformer model
class ModelSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # Optionally, use torch_dtype=torch.float16 (here we convert to half)
            cls._instance = SentenceTransformer(
                "Alibaba-NLP/gte-Qwen2-7B-instruct",
                trust_remote_code=True
            ).to(device_emb)
        return cls._instance

# Load precomputed embeddings and texts from .npy files
hcl_embeddings_matrix = np.load('/sdc/Embedings/site/chat_backend/app/hcl_embeddings.npy')
hcl_texts = np.load('/sdc/Embedings/site/chat_backend/app/hcl_texts.npy', allow_pickle=True)
servicii_embeddings_matrix = np.load('/sdc/Embedings/site/chat_backend/app/servicii_embeddings.npy')
servicii_texts = np.load('/sdc/Embedings/site/chat_backend/app/servicii_texts.npy', allow_pickle=True)

print("NPY embeddings and texts loaded successfully.")

def normalize(embeddings):
    """Normalize embeddings row-wise."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms

# Normalize the embeddings
hcl_embeddings_norm = normalize(hcl_embeddings_matrix).astype('float32')
servicii_embeddings_norm = normalize(servicii_embeddings_matrix).astype('float32')

general_guidelines = (
    "In prima parte a raspunsului sa fie rescrisa in intrebarea, iar mai apoi sa vina raspunsul incepand cu urmatorul rand. "
    "Raspunsul final sa aiba o structura care sa fie usor inteleasa si citita de orice user. "
    "Mentine in raspunsul final explicit și complet denumirea exactă, numărul/anul și articolele precise ale tuturor actelor legislative și regulamentelor relevante (exemplu: O.G. nr.99/2000, H.G. nr.1739/2006, Legea nr.61/1991, Legea nr.215/2001 art.36 alin.(4) lit.e, alin.(6) lit.a pct.7 și 11, H.C.L. nr.102/2009, H.C.L. nr.290/2022, O.U.G. nr.57/2019). "
    "Mentine in raspunsul final toate linkurile care apar in context fara sa modifici in niciun fel aceste linkuri (exemplu: https://www.primariatm.ro/hcl/2009/155, https://servicii.primariatm.ro/dfmt-pj-declararea-instrainarii-terenurilor). "
    "Selectează explicit și strict articolele care pot ajuta la raspunsul unei intrebari care aprobă, abrogă sau modifică direct conținutul legislativ, indicatorii tehnico-economici sau regulamentele existente. "
    "Nu utiliza diacritice, caractere speciale sau spații excesive. "
    "Nu adăuga observații, comentarii personale sau precizări suplimentare care nu ajută la răspunderea întrebării."
)

# Define prompt templates for the two sources and their fusion
HCLS_PROMPT_TEMPLATE = (
    "Întrebarea: {question}\n"
    f"Urmareste cu strictete aceste indrumari:{general_guidelines}\n"
    "In raspunsul final sa ai 2 rubrici care au ajutat la a formula un raspuns:\n"
    "**Referinte**:<exemplu: O.G. nr.99/2000, H.G. nr.1739/2006, Legea nr.61/1991, Legea nr.215/2001 art.36 alin.(4) lit.e, alin.(6) lit.a pct.7 și 11, H.C.L. nr.102/2009, H.C.L. nr.290/2022, O.U.G. nr.57/2019\n>"
    "**Linkuri**:<exemplu: https://www.primariatm.ro/hcl/2009/155, https://servicii.primariatm.ro/dfmt-pj-declararea-instrainarii-terenurilor\n>"
    "Raspunde pe baza acestui context: {docs}"
)
SERVICII_PROMPT_TEMPLATE = (
    "Întrebarea: {question}\n"
    f"Urmareste cu strictete aceste indrumari:{general_guidelines}\n"
    "In raspunsul final sa ai 2 rubrici care au ajutat la a formula un raspuns:\n"
    "**Referinte**:<exemplu: O.G. nr.99/2000, H.G. nr.1739/2006, Legea nr.61/1991, Legea nr.215/2001 art.36 alin.(4) lit.e, alin.(6) lit.a pct.7 și 11, H.C.L. nr.102/2009, H.C.L. nr.290/2022, O.U.G. nr.57/2019\n>"
    "**Linkuri**:<exemplu: https://www.primariatm.ro/hcl/2009/155, https://servicii.primariatm.ro/dfmt-pj-declararea-instrainarii-terenurilor\n>"
    "Raspunde pe baza acest context: {docs}" 
)
FUSION_PROMPT_TEMPLATE = (
    "Întrebarea: {question}\n"
    f"Urmareste cu strictete aceste indrumari:{general_guidelines}\n"
    "In raspunsul final sa ai 2 rubrici care au ajutat la a formula un raspuns:\n"
    "**Referinte**:<exemplu: O.G. nr.99/2000, H.G. nr.1739/2006, Legea nr.61/1991, Legea nr.215/2001 art.36 alin.(4) lit.e, alin.(6) lit.a pct.7 și 11, H.C.L. nr.102/2009, H.C.L. nr.290/2022, O.U.G. nr.57/2019\n>"
    "**Linkuri**:<exemplu: https://www.primariatm.ro/hcl/2009/155, https://servicii.primariatm.ro/dfmt-pj-declararea-instrainarii-terenurilor\n>"
    "Raspunde la intrebare pe baza acestui context {servicii_response}\n{hcls_response} "
)

def get_response(question: str, content: str) -> str:
    """Call Azure OpenAI to generate a response given a prompt built on content."""
    prompt = (
        "Tu esti un asistent virtual menit sa raspunda la intrebarile venite de la public."
        f"Trb sa raspunzi pe baza acestui context={content}"
    )
    print(f"prompt:{prompt}")
    print(f"question:{question}")
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
    )
    return chat_completion.choices[0].message.content

def generate_ai_response(question: str) -> str:
    """Generate an AI response by retrieving similar documents and fusing answers."""
    # Get the singleton model instance
    model = ModelSingleton.get_instance()
    
    # Compute the embedding for the input question
    question_embedding = model.encode([question], convert_to_numpy=True, device=device_emb)
    question_embedding_norm = normalize(question_embedding).astype('float32')
    
    # Compute cosine similarities for both sets of embeddings
    hcl_similarities = cosine_similarity(question_embedding_norm, hcl_embeddings_norm)[0]
    servicii_similarities = cosine_similarity(question_embedding_norm, servicii_embeddings_norm)[0]
    
    # Retrieve top-K similar documents from each set
    hcl_top_indices = np.argsort(hcl_similarities)[::-1][:TOP_K]
    servicii_top_indices = np.argsort(servicii_similarities)[::-1][:TOP_K]
    
    hcl_docs_str = "\n\n".join([hcl_texts[int(idx)] for idx in hcl_top_indices])
    servicii_docs_str = "\n\n".join([servicii_texts[int(idx)] for idx in servicii_top_indices])
    
    # Build prompts for each source based on retrieved context
    hcls_prompt = HCLS_PROMPT_TEMPLATE.format(docs=hcl_docs_str, question=question)
    servicii_prompt = SERVICII_PROMPT_TEMPLATE.format(docs=servicii_docs_str, question=question)
    # print(hcls_prompt)
    
    # Generate responses using the Azure OpenAI client
    hcls_response = get_response(question, hcls_prompt)
    servicii_response = get_response(question, servicii_prompt)
    print(hcls_response)
    
    # Fuse responses into a final answer
    fusion_prompt = FUSION_PROMPT_TEMPLATE.format(
        question=question,
        servicii_response=servicii_response,
        hcls_response=hcls_response,
    )
    final_response = get_response(question, fusion_prompt)
    return final_response

##################################
# Conversation CRUD and Chat API #
##################################

router = APIRouter()

@router.post("/conversations", response_model=Conversation)
async def create_new_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_active_user)
):
    return await create_conversation(
        user_id=current_user.id,
        title=conversation.title,
        messages=[msg.dict() for msg in conversation.messages]
    )

@router.get("/conversations", response_model=List[Conversation])
async def read_conversations(current_user: User = Depends(get_current_active_user)):
    return await get_user_conversations(current_user.id)

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def read_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    conversation = await get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_existing_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_active_user)
):
    conversation = await get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    update_data = {}
    if conversation_update.title is not None:
        update_data["title"] = conversation_update.title
    if conversation_update.messages is not None:
        update_data["messages"] = [m.dict() for m in conversation_update.messages]
    
    updated_conversation = await update_conversation(
        conversation_id=conversation_id,
        update_data=update_data,
        user_id=current_user.id
    )
    return updated_conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    success = await delete_conversation(conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    # Create a user message with a unique ID
    user_message = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": request.message,
        "feedback": None
    }
    
    # Directly generate the AI response using the integrated functionality
    try:
        response_text = generate_ai_response(request.message)
    except Exception as e:
        response_text = f"AI service error: {e}"
    
    ai_message = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": response_text,
        "feedback": None
    }
    
    # If a conversation_id is provided, try to update existing conversation
    if request.conversation_id:
        conversation = await get_conversation(request.conversation_id, current_user.id)
        if conversation:
            # If the conversation title is the default, update it with the text of the first message
            if conversation.title == "New Conversation":
                new_title = request.message[:30] + "..." if len(request.message) > 30 else request.message
                await update_conversation(
                    conversation_id=request.conversation_id,
                    update_data={"title": new_title},
                    user_id=current_user.id
                )
            await add_messages_to_conversation(
                conversation_id=request.conversation_id,
                messages=[user_message, ai_message],
                user_id=current_user.id
            )
            return ChatResponse(
                message=response_text,
                conversation_id=request.conversation_id
            )
    
    # Otherwise, create a new conversation
    title = request.message[:30] + "..." if len(request.message) > 30 else request.message
    conversation = await create_conversation(
        user_id=current_user.id,
        title=title,
        messages=[]
    )
    await add_messages_to_conversation(
        conversation_id=conversation.id,
        messages=[user_message, ai_message],
        user_id=current_user.id
    )
    return ChatResponse(
        message=response_text,
        conversation_id=conversation.id
    )

@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_active_user)
):
    print(f"Received feedback request: {feedback}")
    print(f"Feedback data: {feedback.feedback}")
    
    success = await update_message_feedback(
        conversation_id=feedback.conversation_id,
        message_id=feedback.message_id,
        feedback={
            "qualityRating": feedback.feedback.qualityRating,
            "structureRating": feedback.feedback.structureRating,
            "qualityComment": feedback.feedback.qualityComment,
            "structureComment": feedback.feedback.structureComment
        },
        user_id=current_user.id
    )
    
    if not success:
        print(f"Feedback update failed for message {feedback.message_id} in conversation {feedback.conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation or message not found")
    
    print(f"Feedback successfully saved for message {feedback.message_id}")
    return None

@router.get("/test-feedback/{conversation_id}/{message_id}")
async def test_feedback(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Test endpoint to retrieve a specific message with its feedback.
    This helps verify that the feedback is being stored correctly.
    """
    try:
        conversation = await get_conversation(conversation_id, current_user.id)
        if not conversation:
            return {"error": "Conversation not found", "status_code": 404}
        
        for message in conversation.messages:
            if message.id == message_id:
                return {
                    "success": True,
                    "message": message.content,
                    "role": message.role,
                    "message_id": message.id,
                    "conversation_id": conversation_id,
                    "feedback": message.feedback.dict() if message.feedback else None
                }
        
        return {"error": "Message not found in conversation", "status_code": 404}
    except Exception as e:
        return {"error": f"Error retrieving feedback data: {str(e)}", "status_code": 500}

# Include the conversation-related routes into the main app
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
