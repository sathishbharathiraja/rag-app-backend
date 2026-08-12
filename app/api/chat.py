from fastapi import APIRouter, Depends, HTTPException
import asyncio
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, ConversationHistory, ChatSession
from app.services.rag import similarity_search
from app.core.config import settings

router = APIRouter()

class HistoryItem(BaseModel):
    user_message: str
    ai_response: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None

class ChatResponse(BaseModel):
    response: str
    sources: list[str]
    session_id: int | None = None
    title: str | None = None

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: str

async def call_gemini_api(prompt: str) -> str:
    if not settings.GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY is not set."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                return f"Gemini API Error: {resp.status} - {text}"
            data = await resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return "Failed to parse response from Gemini API"

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Find relevant context
        context_chunks = await similarity_search(db, request.message, current_user.id)
        context = "\n\n".join(context_chunks)
        
        # 2. Formulate prompt
        prompt = f"""Use the following pieces of retrieved context to answer the question. 
If you don't know the answer based on the context, just say that you don't know. 
Provide a comprehensive and detailed answer based on the context provided.

Context:
{context}

Question:
{request.message}

Answer:
"""
        
        # 3. Call LLM directly via REST API
        try:
            response = await asyncio.wait_for(call_gemini_api(prompt), timeout=30.0)
        except asyncio.TimeoutError:
            response = "I am sorry, the request to Gemini timed out."
        except Exception as e:
            print(f"LLM error: {e}")
            response = f"LLM crashed ({e}). Context: " + context[:200] + "..."

        # 4. Filter sources if LLM doesn't know
        response_text = response.lower()
        if "i don't know" in response_text or "i do not know" in response_text or not context_chunks:
            sources_to_return = []
        else:
            sources_to_return = context_chunks

        # 5. Handle Session
        is_new_session = False
        new_title = None
        if request.session_id:
            active_session_id = request.session_id
        else:
            # Generate a title
            try:
                title_prompt = f"Generate a very short title (max 5 words) for this chat based on this first message: {request.message}. Only return the title string."
                new_title = await asyncio.wait_for(call_gemini_api(title_prompt), timeout=10.0)
                new_title = new_title.strip().strip('"')
            except Exception:
                new_title = request.message[:30] + "..."
            
            new_session = ChatSession(user_id=current_user.id, title=new_title)
            db.add(new_session)
            await db.flush()
            active_session_id = new_session.id
            is_new_session = True

        # 6. Save to database
        history_entry = ConversationHistory(
            user_id=current_user.id,
            session_id=active_session_id,
            user_message=request.message,
            ai_response=response
        )
        db.add(history_entry)
        await db.commit()

        return ChatResponse(
            response=response,
            sources=sources_to_return,
            session_id=active_session_id if is_new_session else None,
            title=new_title if is_new_session else None
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=list[ChatSessionResponse])
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.future import select
    stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc())
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat() if s.created_at else ""
        )
        for s in sessions
    ]

@router.get("/sessions/{session_id}/history", response_model=list[HistoryItem])
async def get_session_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.future import select
    stmt = select(ConversationHistory).where(
        ConversationHistory.user_id == current_user.id,
        ConversationHistory.session_id == session_id
    ).order_by(ConversationHistory.timestamp.asc())
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    return [
        HistoryItem(
            user_message=item.user_message,
            ai_response=item.ai_response,
            timestamp=item.timestamp.isoformat() if item.timestamp else ""
        )
        for item in history
    ]

# Keep the original /history for backward compatibility just in case
@router.get("/history", response_model=list[HistoryItem])
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.future import select
    stmt = select(ConversationHistory).where(ConversationHistory.user_id == current_user.id).order_by(ConversationHistory.timestamp.asc())
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    return [
        HistoryItem(
            user_message=item.user_message,
            ai_response=item.ai_response,
            timestamp=item.timestamp.isoformat() if item.timestamp else ""
        )
        for item in history
    ]
