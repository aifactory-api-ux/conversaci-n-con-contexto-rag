from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from backend.query_service.models.query import QueryRequest, QueryResponse
from backend.query_service.models.response import QueryHistoryResponse
from backend.query_service.service import QueryService
from shared.security import verify_token, get_current_user_id
from shared.exceptions import AuthenticationException, ValidationException

router = APIRouter()
security = HTTPBearer()

async def get_query_service() -> QueryService:
    """Dependency to get QueryService instance."""
    return QueryService()

async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify JWT token and return user ID."""
    token = credentials.credentials
    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationException("Invalid token payload")
        return user_id
    except Exception as e:
        raise AuthenticationException(f"Authentication failed: {str(e)}")

@router.post(
    "/",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a query with RAG",
    description="Process a user query using retrieval-augmented generation. The system will retrieve relevant document chunks and generate a contextual response."
)
async def process_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
    user_id: str = Depends(verify_auth)
) -> QueryResponse:
    """
    Process a query using RAG pipeline.
    
    Steps:
    1. Generate embedding for the query
    2. Search for similar document chunks
    3. Retrieve conversation history
    4. Generate response using LLM
    5. Cache the response
    6. Store the message in conversation
    """
    try:
        # Validate conversation belongs to user
        # This would typically call conversation service
        # For now, we'll trust the conversation_id
        
        # Process the query
        response = await query_service.process_query(
            user_id=user_id,
            conversation_id=request.conversation_id,
            query=request.message,
            include_sources=request.include_sources
        )
        
        return response
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )

@router.get(
    "/history/{conversation_id}",
    response_model=QueryHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get query history for conversation",
    description="Retrieve the history of queries and responses for a specific conversation."
)
async def get_query_history(
    conversation_id: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    query_service: QueryService = Depends(get_query_service),
    user_id: str = Depends(verify_auth)
) -> QueryHistoryResponse:
    """
    Get query history for a conversation.
    
    Returns paginated list of query-response pairs.
    """
    try:
        # Validate conversation belongs to user
        # This would typically call conversation service
        
        # Get query history
        history = await query_service.get_query_history(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve query history: {str(e)}"
        )

@router.delete(
    "/cache/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Clear cache for conversation",
    description="Clear cached query responses for a specific conversation."
)
async def clear_conversation_cache(
    conversation_id: str,
    query_service: QueryService = Depends(get_query_service),
    user_id: str = Depends(verify_auth)
):
    """
    Clear cache for a conversation.
    """
    try:
        # Validate conversation belongs to user
        
        # Clear cache
        await query_service.clear_conversation_cache(
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return {"message": "Cache cleared successfully"}
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )
