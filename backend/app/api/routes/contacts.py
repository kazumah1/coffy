from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
import json
from app.services.database_service import DatabaseService
from app.dependencies import get_database_service
import re

def standardize_phone_number(phone: str) -> str:
    digits = re.sub(r'[^0-9]', '', phone)
    if not digits.startswith('1'):
        digits = '1' + digits
    return f'+{digits}'

router = APIRouter()

class PhoneNumber(BaseModel):
    number: str

class Email(BaseModel):
    email: str

class Contact(BaseModel):
    id: str
    name: str
    phoneNumbers: Optional[List[PhoneNumber]] = []
    emails: Optional[List[Email]] = []

class ContactsSyncRequest(BaseModel):
    user_id: str
    contacts: List[Contact]

class BestFriendsSaveRequest(BaseModel):
    user_id: str
    best_friends: List[Contact]

@router.post("/sync")
async def sync_contacts(
    request: ContactsSyncRequest,
    db_service: DatabaseService = Depends(get_database_service),
):
    """Sync user's device contacts with the backend"""
    try:
        # Get existing contacts for the user
        existing_contacts = await db_service.get_user_contacts(request.user_id)
        existing_contact_map = {c["phone_number"]: c for c in existing_contacts}
        
        # Process each contact from the device
        for contact in request.contacts:
            # TODO: allow multiple phone numbers
            if contact.phoneNumbers[0].number in existing_contact_map:
                contact_data = {
                    "name": contact.name,
                    "phone_number": standardize_phone_number(contact.phoneNumbers[0].number)
                }
                # Update existing contact
                await db_service.update_contact(existing_contact_map[contact.phoneNumbers[0].number]["id"], contact_data)
            else:
                # Create new contact
                contact_data = {
                    "owner_id": request.user_id,
                    "name": contact.name,
                    "phone_number": standardize_phone_number(contact.phoneNumbers[0].number)
                }
                await db_service.create_contact(contact_data)
        
        return {"success": True, "message": f"Synced {len(request.contacts)} contacts"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing contacts: {str(e)}")

# TODO: not for MVP
@router.get("/best-friends/{user_id}")
async def get_contacts_and_best_friends(
    user_id: str,
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get all contacts with best friend status"""
    try:
        # Get all contacts for the user
        contacts = await db_service.get_user_contacts(user_id)
        
        # Get best friends for the user
        best_friends = await db_service.get_best_friends(user_id)
        best_friend_ids = {bf["contact_id"] for bf in best_friends}
        
        # Format contacts with best friend status
        formatted_contacts = []
        for contact in contacts:
            phone_numbers = []
            emails = []
            
            # Parse phone numbers and emails from JSON if they exist
            if contact.get("phone_numbers"):
                if isinstance(contact["phone_numbers"], str):
                    phone_list = json.loads(contact["phone_numbers"])
                else:
                    phone_list = contact["phone_numbers"]
                phone_numbers = [{"number": phone} for phone in phone_list]
            
            if contact.get("emails"):
                if isinstance(contact["emails"], str):
                    email_list = json.loads(contact["emails"])
                else:
                    email_list = contact["emails"]
                emails = [{"email": email} for email in email_list]
            
            formatted_contact = {
                "id": contact["device_contact_id"],
                "name": contact["name"],
                "phoneNumbers": phone_numbers,
                "emails": emails,
                "isBestFriend": contact["id"] in best_friend_ids
            }
            formatted_contacts.append(formatted_contact)
        
        return {"success": True, "contacts": formatted_contacts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting contacts: {str(e)}")

# TODO: not for MVP
@router.post("/best-friends/save")
async def save_best_friends(
    request: BestFriendsSaveRequest,
    db_service: DatabaseService = Depends(get_database_service),
):
    """Save user's best friends selection"""
    try:
        # First, clear existing best friends for this user
        await db_service.clear_best_friends(request.user_id)
        
        # Add new best friends
        for friend in request.best_friends:
            # Get the contact from database using device_contact_id
            contact = await db_service.get_contact_by_device_id(request.user_id, friend.id)
            
            if contact:
                await db_service.add_best_friend(request.user_id, contact["id"])
        
        return {"success": True, "message": f"Saved {len(request.best_friends)} best friends"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving best friends: {str(e)}")

# TODO: not for MVP
@router.get("/best-friends/list/{user_id}")
async def get_best_friends_list(
    user_id: str,
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get list of user's best friends"""
    try:
        best_friends = await db_service.get_best_friends_with_details(user_id)
        
        formatted_friends = []
        for friend in best_friends:
            phone_numbers = []
            emails = []
            
            # Parse phone numbers and emails from JSON if they exist
            if friend.get("phone_numbers"):
                if isinstance(friend["phone_numbers"], str):
                    phone_list = json.loads(friend["phone_numbers"])
                else:
                    phone_list = friend["phone_numbers"]
                phone_numbers = [{"number": phone} for phone in phone_list]
            
            if friend.get("emails"):
                if isinstance(friend["emails"], str):
                    email_list = json.loads(friend["emails"])
                else:
                    email_list = friend["emails"]
                emails = [{"email": email} for email in email_list]
            
            formatted_friend = {
                "id": friend["device_contact_id"],
                "name": friend["name"],
                "phoneNumbers": phone_numbers,
                "emails": emails
            }
            formatted_friends.append(formatted_friend)
        
        return {"success": True, "best_friends": formatted_friends}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting best friends: {str(e)}") 