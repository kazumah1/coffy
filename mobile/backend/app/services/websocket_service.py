from fastapi import WebSocket
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

async def send_chat_message(user_id: str, message: str):
    """Send a chat message to a specific user's WebSocket connection."""
    try:
        if user_id in active_connections:
            await active_connections[user_id].send_json({
                "type": "chat_message",
                "message": message
            })
            logger.info(f"Sent chat message to user {user_id}")
        else:
            logger.warning(f"No active WebSocket connection for user {user_id}")
    except Exception as e:
        logger.error(f"Error sending chat message to user {user_id}: {str(e)}")
        raise 