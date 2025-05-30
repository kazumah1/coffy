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

CREATE_AVAILABILITY_CONVERSATION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_availability_conversation",
        "description": "Create a new SMS conversation for getting availability and preferences from a user. Works for both registered and unregistered users. For registered users, this creates a shorter conversation to confirm availability and preferences. For unregistered users, this creates a more detailed conversation to collect availability through SMS.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user"
                },
                "user_name": {
                    "type": "string",
                    "description": "Name of the user"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional UUID of the registered user. If provided, creates a shorter conversation for registered users."
                }
            },
            "required": ["phone_number", "user_name"]
        }
    }
}

CREATE_UNREGISTERED_TIME_SLOTS_TOOL = {
    "type": "function",
    "function": {
        "name": "create_unregistered_time_slots",
        "description": "Store time slots (busy or available) for an unregistered user based on their text responses. This must be called after creating the availability conversation and receiving their response.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the unregistered user"
                },
                "time_slots": {
                    "type": "array",
                    "description": "List of time slots extracted from user's messages",
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
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence score for the slot (0-1), optional"
                            },
                            "raw_text": {
                                "type": "string",
                                "description": "Original text that generated this slot, optional"
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

SEND_AVAILABILITY_REQUEST_TOOL = {
    "type": "function",
    "function": {
        "name": "send_availability_request",
        "description": "Send an initial availability request to an unregistered user via SMS. This must be called after creating the event participant and availability conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the unregistered user"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD) for availability window"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD) for availability window"
                },
                "event_title": {
                    "type": "string",
                    "description": "Title of the event to include in the message"
                }
            },
            "required": ["phone_number", "start_date", "end_date", "event_title"]
        }
    }
}

PARSE_AVAILABILITY_RESPONSE_TOOL = {
    "type": "function",
    "function": {
        "name": "parse_availability_response",
        "description": "Parse a user's response to an availability request. For registered users, this checks if they've given permission to access their calendar. For unregistered users, this extracts time slots from their text response.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user"
                },
                "response_text": {
                    "type": "string",
                    "description": "The user's response text to parse"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional UUID of the registered user. If provided, checks for calendar permission."
                }
            },
            "required": ["phone_number", "response_text"]
        }
    }
}

SCHEDULE_EVENT_TOOL = {
    "type": "function",
    "function": {
        "name": "schedule_event",
        "description": "Finalize event details and notify participants. This tool is used when all availability has been collected and a final time has been chosen.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to schedule"
                },
                "final_time": {
                    "type": "string",
                    "description": "Final event time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                "location": {
                    "type": "string",
                    "description": "Optional location for the event"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the event in minutes (default: 60)"
                }
            },
            "required": ["event_id", "final_time"]
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
                    "description": "Phone number of the participant to invite"
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

HANDLE_EVENT_RESPONSE_TOOL = {
    "type": "function",
    "function": {
        "name": "handle_event_response",
        "description": "Process participant responses to event invitations. This tool parses responses like 'yes', 'no', or custom messages and updates participant status accordingly.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the participant responding"
                },
                "response_text": {
                    "type": "string",
                    "description": "The participant's response text to parse"
                }
            },
            "required": ["event_id", "phone_number", "response_text"]
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
                    "description": "Phone number of the participant to remind"
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

# List of all available tools
AVAILABLE_TOOLS = [
    CREATE_DRAFT_EVENT_TOOL,
    CREATE_EVENT_PARTICIPANT_TOOL,
    SEARCH_CONTACTS_TOOL,
    GET_GOOGLE_CALENDAR_BUSY_TIMES_TOOL,
    CREATE_AVAILABILITY_CONVERSATION_TOOL,
    CREATE_UNREGISTERED_TIME_SLOTS_TOOL,
    CHECK_USER_REGISTRATION_TOOL,
    SEND_AVAILABILITY_REQUEST_TOOL,
    PARSE_AVAILABILITY_RESPONSE_TOOL,
    SCHEDULE_EVENT_TOOL,
    SEND_EVENT_INVITATION_TOOL,
    HANDLE_EVENT_RESPONSE_TOOL,
    SEND_REMINDER_TOOL,
    HANDLE_SCHEDULING_CONFLICT_TOOL,
    # Add more tools here as they are implemented
] 