function handleCredentialResponse(response) {
    // Send the token to our backend
    fetch('/api/auth/google', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            credential: response.credential
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.access_token) {
            // Store the token
            localStorage.setItem('token', data.access_token);
            
            // Show success animation
            showSuccessAnimation().then(() => {
                // Redirect to main app
                window.location.href = '/';
            });
        } else {
            showError('Authentication failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Something went wrong. Please try again.');
    });
}

function showSuccessAnimation() {
    return new Promise((resolve) => {
        // Create success overlay
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        
        const content = document.createElement('div');
        content.className = 'bg-white rounded-2xl p-8 flex flex-col items-center transform scale-0 transition-transform duration-300';
        content.innerHTML = `
            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">Successfully Logged In!</h3>
            <p class="text-gray-600">Redirecting to your dashboard...</p>
        `;
        
        overlay.appendChild(content);
        document.body.appendChild(overlay);
        
        // Trigger animation
        setTimeout(() => {
            content.style.transform = 'scale(1)';
        }, 100);
        
        // Resolve after animation
        setTimeout(resolve, 1500);
    });
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded';
    errorDiv.innerHTML = `
        <strong class="font-bold">Error!</strong>
        <p>${message}</p>
    `;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
} 