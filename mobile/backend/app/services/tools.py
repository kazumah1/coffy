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
            },
            "required": ["query"]
        }
    }
}

GET_GOOGLE_CALENDAR_BUSY_TIMES_TOOL = {
    "type": "function",
    "function": {
        "name": "get_google_calendar_busy_times",
        "description": "Get busy times from a registered user's Google Calendar within a date range. This is for registered participants. This tool returns times when the user is NOT available (has events). This tool can ONLY be used for registered users (those with a valid UUID). For unregistered users, use the texting-based availability flow instead.",
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

GET_CREATOR_GOOGLE_CALENDAR_BUSY_TIMES_TOOL = {
    "type": "function",
    "function": {
        "name": "get_creator_google_calendar_busy_times",
        "description": "Get busy times from the creator's Google Calendar within a date range. This tool must always be used once per event to find a time that works best for the creator. This tool must only be used after an event has been created.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "UUID of the creator of the event. Sometimes referred to as 'owner_id' or 'creator_id' in the database."
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
        "description": "Create a new SMS conversation to check if a user is interested in an event. This is the first step in the availability collection process. If the conversation already exists, returns the existing conversation.",
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
                "start": {
                    "type": "object",
                    "description": "Final event start time in ISO format (YYYY-MM-DDTHH:MM:SS)",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date of the event in ISO format (YYYY-MM-DD)"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Timezone of the event in IANA format"
                        },
                        "dateTime": {
                            "type": "string",
                            "description": "Final event start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                        },
                    }
                },
                "end": {
                    "type": "object",
                    "description": "Final event end time in ISO format (YYYY-MM-DDTHH:MM:SS)",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date of the event in ISO format (YYYY-MM-DD)"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Timezone of the event in IANA format"
                        },
                        "dateTime": {
                            "type": "string",
                            "description": "Final event end time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                        },
                    }
                },
                "location": {
                    "type": "string",
                    "description": "Optional location for the event"
                },
                "creator_message": {
                    "type": "string",
                    "description": "Message to send to the creator after the event has been scheduled. Will be sent directly to the creator."
                }
            },
            "required": ["event_id", "start", "end", "creator_message"]
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

SEND_TEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "send_text",
        "description": "Send a text message to event participants. Use final=True for final messages that don't expect a response.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number to send the message to"
                },
                "message": {
                    "type": "string",
                    "description": "Message to send"
                },
                "final": {
                    "type": "boolean",
                    "description": "Whether this is a final message that doesn't expect a response. Not necessary for most messages.",
                    "default": False
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
        "description": "Send a chat message to the creator via the app if more information or confirmation is needed. Also used for confirming the contacts are the correct ones.",
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

GET_EVENT_AVAILABILITIES_TOOL = {
    "type": "function",
    "function": {
        "name": "get_event_availabilities",
        "description": "Get the availabilities of all participants for an event",
        "parameters": {
            "type": "object", 
            "properties": {
                "event_id": {"type": "string", "description": "The event's ID"}
            }, 
            "required": ["event_id"]}
    }
}

STOP_LOOP_TOOL = {
    "type": "function",
    "function": {
        "name": "stop_loop",
        "description": "Stop the agent loop. Used to stop the agent loop when all tasks are complete.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


# List of all available tools
AVAILABLE_TOOLS = [
    CREATE_DRAFT_EVENT_TOOL,
    SEARCH_CONTACTS_TOOL,
    CHECK_USER_REGISTRATION_TOOL,
    CREATE_EVENT_PARTICIPANT_TOOL,
    CREATE_OR_GET_CONVERSATION_TOOL,
    HANDLE_CONFIRMATION_TOOL,
    SEND_TEXT_TOOL,
    GET_GOOGLE_CALENDAR_BUSY_TIMES_TOOL,
    GET_CREATOR_GOOGLE_CALENDAR_BUSY_TIMES_TOOL,
    CREATE_UNREGISTERED_TIME_SLOTS_TOOL,
    CREATE_FINAL_TIME_SLOTS_TOOL,
    SCHEDULE_EVENT_TOOL,
    SEND_EVENT_INVITATION_TOOL,
    HANDLE_SCHEDULING_CONFLICT_TOOL,
    SEND_CHAT_MESSAGE_TO_USER_TOOL,
    GET_EVENT_AVAILABILITIES_TOOL,
    STOP_LOOP_TOOL,
]

# Dictionary mapping tool names to their indices in AVAILABLE_TOOLS
TOOL_INDICES = {
    "create_draft_event": 0,
    "search_contacts": 1,
    "check_user_registration": 2,
    "create_event_participant": 3,
    "create_or_get_conversation": 4,
    "handle_confirmation": 5,
    "send_text": 6,
    "get_google_calendar_busy_times": 7,
    "get_creator_google_calendar_busy_times": 8,
    "create_unregistered_time_slots": 9,
    "create_final_time_slots": 10,
    "schedule_event": 11,
    "send_event_invitation": 12,
    "handle_scheduling_conflict": 13,
    "send_chat_message_to_user": 14,
    "get_event_availabilities": 15,
    "stop_loop": 16,
} 