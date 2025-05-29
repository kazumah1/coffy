document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const voiceButton = document.getElementById('voice-button');
    const emojiButton = document.getElementById('emoji-button');
    const imageButton = document.getElementById('image-button');

    // Show initial assistant message
    addMessage('assistant', 'Hi! I can help you schedule meetups with your friends. Just tell me what you want to plan.', true);

    // Handle message input
    messageInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter' && messageInput.value.trim()) {
            const message = messageInput.value.trim();
            messageInput.value = '';
            
            // Add user message to chat
            addMessage('user', message);

            // Simulate typing indicator
            const typingIndicator = addTypingIndicator();

            try {
                // Send message to backend
                const response = await sendMessage(message);
                
                // Remove typing indicator
                typingIndicator.remove();

                // Add assistant's response
                addMessage('assistant', response.message);

                // If there are follow-up questions or suggestions, add them
                if (response.suggestions) {
                    response.suggestions.forEach(suggestion => {
                        addSuggestionBubble(suggestion);
                    });
                }

                // If a meeting was scheduled, show confirmation
                if (response.scheduledMeeting) {
                    addScheduleConfirmation(response.scheduledMeeting);
                }

            } catch (error) {
                console.error('Error:', error);
                typingIndicator.remove();
                addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            }
        }
    });

    // Helper function to add a message to the chat
    function addMessage(type, text, isInitial = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${type}-message`;
        
        if (type === 'assistant' && !isInitial) {
            // Add the people icon for assistant messages
            const iconDiv = document.createElement('div');
            iconDiv.className = 'flex items-center justify-center mb-2';
            iconDiv.innerHTML = `
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>`;
            messageDiv.appendChild(iconDiv);
        }

        messageDiv.appendChild(document.createTextNode(text));
        chatContainer.querySelector('.max-w-4xl').appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper function to add a typing indicator
    function addTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message-bubble assistant-message';
        indicatorDiv.innerHTML = `
            <div class="flex gap-2">
                <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
            </div>`;
        chatContainer.querySelector('.max-w-4xl').appendChild(indicatorDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return indicatorDiv;
    }

    // Helper function to add suggestion bubbles
    function addSuggestionBubble(suggestion) {
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble assistant-message cursor-pointer hover:bg-gray-200 transition-colors';
        bubbleDiv.textContent = suggestion;
        bubbleDiv.onclick = () => {
            messageInput.value = suggestion;
            messageInput.focus();
        };
        chatContainer.querySelector('.max-w-4xl').appendChild(bubbleDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper function to add schedule confirmation
    function addScheduleConfirmation(meeting) {
        const confirmationDiv = document.createElement('div');
        confirmationDiv.className = 'message-bubble assistant-message bg-green-100';
        confirmationDiv.innerHTML = `
            <div class="font-semibold">Meeting Scheduled! 🎉</div>
            <div class="mt-2">
                <div>📅 ${meeting.date}</div>
                <div>⏰ ${meeting.time}</div>
                <div>👥 ${meeting.participants.join(', ')}</div>
                ${meeting.location ? `<div>📍 ${meeting.location}</div>` : ''}
            </div>`;
        chatContainer.querySelector('.max-w-4xl').appendChild(confirmationDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper function to send message to backend
    async function sendMessage(message) {
        // TODO: Replace with actual API endpoint
        // For now, return mock responses
        return new Promise((resolve) => {
            setTimeout(() => {
                if (message.toLowerCase().includes('dinner')) {
                    resolve({
                        message: "I'll help you schedule a dinner. Let me check everyone's availability.",
                        suggestions: [
                            "Yes, that works for me",
                            "Can we do it earlier?",
                            "Let's try another day"
                        ]
                    });
                } else {
                    resolve({
                        message: "I can help you schedule that. What time were you thinking?",
                        suggestions: [
                            "This afternoon",
                            "Tomorrow morning",
                            "Next week"
                        ]
                    });
                }
            }, 1000);
        });
    }
}); 