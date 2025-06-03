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
                    "description": "UUID of the event creator. Could also be listed as 'owner_id' in the database or other tools."
                },
                "title": {
                    "type": "string",
                    "description": "Title of the event. Create a title based on the initial user input."
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

SEARCH_CONTACTS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_contacts",
        "description": "Search for contacts by name, phone number, or relationship",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for name or phone number"
                },
                "min_relationship_score": {
                    "type": "number",
                    "description": "Minimum relationship score (0-100)"
                },
                "recent_only": {
                    "type": "boolean",
                    "description": "Only return contacts with recent interactions"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return"
                },
                "days_ago": {
                    "type": "integer",
                    "description": "Number of days ago to consider for recent interactions (default 30)"
                }
            }
        }
    }
}

GET_GOOGLE_CALENDAR_BUSY_TIMES_TOOL = {
    "type": "function",
    "function": {
        "name": "get_google_calendar_busy_times",
        "description": "Get busy times from a registered user's Google Calendar within a date range. This tool returns times when the user is NOT available (has events). This tool can ONLY be used for registered users (those with a valid UUID). For unregistered users, use the texting-based availability flow instead.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "UUID of the registered user whose calendar to check. This must be a registered user with a valid UUID (not an unregistered participant)."
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD)"
                }
            },
            "required": ["user_id", "start_date", "end_date"]
        }
    }
}

CREATE_OR_GET_CONVERSATION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_or_get_conversation",
        "description": "Create a new SMS conversation to check if a user is interested in an event. This is the first step in the availability collection process. After creating the conversation, the user will be asked if they are interested in the event through an SMS message. If the conversation already exists, return the conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user. Format: '+15551234567'"
                },
                "user_name": {
                    "type": "string",
                    "description": "Name of the user as it appears in their contact"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional UUID of recipient. Must be provided if the user is registered. Must not be provided if the user is unregistered. Not the same as the creator/owner_id."
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD) for availability window"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD) for availability window"
                },
                "message": {
                    "type": "string",
                    "description": "Initial SMS text message to send to the user. Should be short and concise. Include the owner_name/creator_name but not the owner_id/creator_id in the message."
                }
            },
            "required": ["phone_number", "user_name", "start_date", "end_date", "message"]
        }
    }
}

CREATE_UNREGISTERED_TIME_SLOTS_TOOL = {
    "type": "function",
    "function": {
        "name": "create_unregistered_time_slots",
        "description": "Store time slots for an unregistered user. The LLM should have already parsed and formatted the time slots correctly.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the unregistered user. Format: '+15551234567'"
                },
                "time_slots": {
                    "type": "array",
                    "description": "List of time slots that the LLM has already parsed and formatted",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                            },
                            "slot_type": {
                                "type": "string",
                                "description": "Type of slot: 'busy' or 'available'",
                                "enum": ["busy", "available"]
                            }
                        },
                        "required": ["start_time", "end_time", "slot_type"]
                    }
                }
            },
            "required": ["phone_number", "time_slots"]
        }
    }
}

CHECK_USER_REGISTRATION_TOOL = {
    "type": "function",
    "function": {
        "name": "check_user_registration",
        "description": "Check if a phone number belongs to a registered user. This is used to determine which flow to use (Google Calendar vs SMS) for availability collection.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number to check for registration status"
                }
            },
            "required": ["phone_number"]
        }
    }
}

HANDLE_CONFIRMATION_TOOL = {
    "type": "function",
    "function": {
        "name": "handle_confirmation",
        "description": "Update conversation and participant status based on user's confirmation response. The LLM should have already determined if the user confirmed or declined. This is used in the confirmation stage of the conversation flow.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user. Format: '+15551234567'"
                },
                "confirmation": {
                    "type": "boolean",
                    "description": "Whether or not the user confirmed interest in the event. True if confirmed, False if declined."
                },
                "message": {
                    "type": "string",
                    "description": "The user's response message (for record keeping)"
                }
            },
            "required": ["phone_number", "confirmation", "message"]
        }
    }
}

CREATE_FINAL_TIME_SLOTS_TOOL = {
    "type": "function",
    "function": {
        "name": "create_final_time_slots",
        "description": "Store final time slots once the LLM has collected all necessary information. The LLM should have already formatted the time slots correctly.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user. Format: '+15551234567'"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional UUID of the registered user"
                },
                "time_slots": {
                    "type": "array",
                    "description": "List of final time slots that the LLM has already formatted",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                            },
                            "slot_type": {
                                "type": "string",
                                "description": "Type of slot: 'busy' or 'available'",
                                "enum": ["busy", "available"]
                            }
                        },
                        "required": ["start_time", "end_time", "slot_type"]
                    }
                }
            },
            "required": ["phone_number", "time_slots"]
        }
    }
}

SCHEDULE_EVENT_TOOL = {
    "type": "function",
    "function": {
        "name": "schedule_event",
        "description": "Finalize event details and notify the participants, including the creator. This tool is used when all availability has been collected and a final time has been chosen.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to schedule"
                },
                "final_start": {
                    "type": "string",
                    "description": "Final event start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                "final_end": {
                    "type": "string",
                    "description": "Final event end time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                "location": {
                    "type": "string",
                    "description": "Optional location for the event"
                },
                "creator_message": {
                    "type": "string",
                    "description": "Message to send to the creator after the event has been scheduled"
                }
            },
            "required": ["event_id", "final_start", "final_end", "creator_message"]
        }
    }
}

SEND_EVENT_INVITATION_TOOL = {
    "type": "function",
    "function": {
        "name": "send_event_invitation",
        "description": "Send event details to participants once finalized. This tool is used to send a formal invitation to participants after the event has been scheduled.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the scheduled event"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the participant to invite. Format: '+15551234567'"
                },
                "include_ics": {
                    "type": "boolean",
                    "description": "Whether to include an ICS calendar file for registered users (default: true)"
                }
            },
            "required": ["event_id", "phone_number"]
        }
    }
}

SEND_REMINDER_TOOL = {
    "type": "function",
    "function": {
        "name": "send_reminder",
        "description": "Send a reminder about an upcoming event to participants. Different reminder types (day_before, hour_before) use different message templates.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to send reminder for"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the participant to remind. Format: '+15551234567'"
                },
                "reminder_type": {
                    "type": "string",
                    "description": "Type of reminder to send",
                    "enum": ["day_before", "hour_before"]
                }
            },
            "required": ["event_id", "phone_number", "reminder_type"]
        }
    }
}

HANDLE_SCHEDULING_CONFLICT_TOOL = {
    "type": "function",
    "function": {
        "name": "handle_scheduling_conflict",
        "description": "Handle cases where no common time is found for all participants. Suggests alternative times or asks for more availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event with scheduling conflict"
                },
                "participant_phone_numbers": {
                    "type": "array",
                    "description": "List of phone numbers for participants to contact about the conflict",
                    "items": {
                        "type": "string"
                    }
                },
                "conflict_type": {
                    "type": "string",
                    "description": "Type of conflict to handle",
                    "enum": ["no_common_time", "insufficient_availability", "time_preference_conflict"]
                }
            },
            "required": ["event_id", "participant_phone_numbers", "conflict_type"]
        }
    }
}

SEND_CONFIRMATION_TEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "send_confirmation_text",
        "description": "Send a text message specifically for confirming interest in an event. This is used in the initial confirmation stage of event planning. The message should ask if the user is interested in the event.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user to send the message to. Format: '+15551234567'"
                },
                "message": {
                    "type": "string",
                    "description": "The confirmation message to send. Should ask if the user is interested in the event. Example: 'Are you down?'"
                }
            },
            "required": ["phone_number", "message"]
        }
    }
}

SEND_AVAILABILITY_TEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "send_availability_text",
        "description": "Send a text message specifically for collecting availability information. This is used after a user has confirmed interest in an event. The message should ask for days and times when the user is available.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user to send the message to. Format: '+15551234567'"
                },
                "message": {
                    "type": "string",
                    "description": "The availability request message to send. Should ask for days and times when the user is available. Example: 'What days and times work for you?"
                }
            },
            "required": ["phone_number", "message"]
        }
    }
}

SEND_FINAL_TEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "send_final_text",
        "description": "Send a text message for final event details or notifications that don't require a response. This is used in the scheduling stage for sending scheduled event details, reminders, or other one-way communications.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user to send the message to. Format: '+15551234567'"
                },
                "message": {
                    "type": "string",
                    "description": "The final message to send. Should contain complete event details or notification information."
                }
            },
            "required": ["phone_number", "message"]
        }
    }
}

SEND_CHAT_MESSAGE_TO_USER_TOOL = {
    "type": "function",
    "function": {
        "name": "send_chat_message_to_user",
        "description": "Send a chat message to the user via the app if more information is needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The user's ID"},
                "message": {"type": "string", "description": "The message to send"}
            },
            "required": ["user_id", "message"]
        }
    }
}

# List of all available tools
AVAILABLE_TOOLS = [
    CREATE_DRAFT_EVENT_TOOL,
    CREATE_EVENT_PARTICIPANT_TOOL,
    SEARCH_CONTACTS_TOOL,
    GET_GOOGLE_CALENDAR_BUSY_TIMES_TOOL,
    CREATE_OR_GET_CONVERSATION_TOOL,
    CHECK_USER_REGISTRATION_TOOL,
    HANDLE_CONFIRMATION_TOOL,
    CREATE_UNREGISTERED_TIME_SLOTS_TOOL,
    CREATE_FINAL_TIME_SLOTS_TOOL,
    SCHEDULE_EVENT_TOOL,
    SEND_EVENT_INVITATION_TOOL,
    SEND_REMINDER_TOOL,
    HANDLE_SCHEDULING_CONFLICT_TOOL,
    SEND_CONFIRMATION_TEXT_TOOL,
    SEND_AVAILABILITY_TEXT_TOOL,
    SEND_FINAL_TEXT_TOOL,
    SEND_CHAT_MESSAGE_TO_USER_TOOL,
]

# Dictionary mapping tool names to their indices in AVAILABLE_TOOLS
TOOL_NAME_TO_INDEX = {
    "create_draft_event": 0,
    "create_event_participant": 1,
    "search_contacts": 2,
    "get_google_calendar_busy_times": 3,
    "create_or_get_conversation": 4,
    "check_user_registration": 5,
    "handle_confirmation": 6,
    "create_unregistered_time_slots": 7,
    "create_final_time_slots": 8,
    "schedule_event": 9,
    "send_event_invitation": 10,
    "send_reminder": 11,
    "handle_scheduling_conflict": 12,
    "send_confirmation_text": 13,
    "send_availability_text": 14,
    "send_final_text": 15,
    "send_chat_message_to_user": 16
} 