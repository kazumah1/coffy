"""Tool definitions for OpenRouter function calling."""

CREATE_DRAFT_EVENT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_draft_event",
        "description": "Create a draft event that can be completed later with more details",
        "parameters": {
            "type": "object",
            "properties": {
                "creator_id": {
                    "type": "string",
                    "description": "UUID of the event creator"
                },
                "title": {
                    "type": "string",
                    "description": "Title of the event"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the event"
                }
            },
            "required": ["creator_id", "title"]
        }
    }
}

CREATE_EVENT_PARTICIPANT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_event_participant",
        "description": "Create a participant for an event",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the participant"
                },
                "name": {
                    "type": "string",
                    "description": "Contact name of the participant"
                }
            },
            "required": ["phone_number", "name"]
        }
    }
}

# List of all available tools
AVAILABLE_TOOLS = [
    CREATE_DRAFT_EVENT_TOOL,
    CREATE_EVENT_PARTICIPANT_TOOL,
    # Add more tools here as they are implemented
] 