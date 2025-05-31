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
        "description": "Create a new SMS conversation to check if a user is interested in an event. This is the first step in the availability collection process. After creating the conversation, the user will be asked if they are interested in the event through an SMS message.",
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
                },
                "start_date": {
                    "type": "string",
                    "description": "Optional start date in ISO format (YYYY-MM-DD) for availability window"
                },
                "end_date": {
                    "type": "string",
                    "description": "Optional end date in ISO format (YYYY-MM-DD) for availability window"
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
        "description": "Store time slots for an unregistered user. The LLM should have already parsed and formatted the time slots correctly.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the unregistered user"
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

PARSE_CONFIRMATION_TOOL = {
    "type": "function",
    "function": {
        "name": "parse_confirmation",
        "description": "Update conversation and participant status based on user's confirmation response. The LLM should have already determined if the user confirmed or declined.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user"
                },
                "confirmation": {
                    "type": "boolean",
                    "description": "Whether the user confirmed interest in the event"
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

SEND_TEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "send_text",
        "description": "Send a text message to a user. This is used for sending follow-up questions or responses.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the user to send the message to"
                },
                "message": {
                    "type": "string",
                    "description": "The message to send"
                }
            },
            "required": ["phone_number", "message"]
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
                    "description": "Phone number of the user"
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

CHECK_CONVERSATION_STATE_TOOL = {
    "type": "function",
    "function": {
        "name": "check_conversation_state",
        "description": "Check the current state of the conversation and determine if the loop should continue or stop. This tool helps manage the flow of the conversation and ensures all necessary steps are completed.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the current event"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the current participant"
                },
                "current_stage": {
                    "type": "string",
                    "description": "Current stage of the conversation (e.g., 'initial_contact', 'availability_collection', 'scheduling', 'confirmation')"
                }
            },
            "required": ["event_id", "phone_number", "current_stage"]
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
    CHECK_USER_REGISTRATION_TOOL,
    PARSE_CONFIRMATION_TOOL,
    SEND_TEXT_TOOL,
    CREATE_UNREGISTERED_TIME_SLOTS_TOOL,
    CREATE_FINAL_TIME_SLOTS_TOOL,
    SCHEDULE_EVENT_TOOL,
    SEND_EVENT_INVITATION_TOOL,
    SEND_REMINDER_TOOL,
    HANDLE_SCHEDULING_CONFLICT_TOOL,
    CHECK_CONVERSATION_STATE_TOOL,
] 