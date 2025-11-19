// // Global variables
// let currentPage = 1;
// let currentQuery = '';
// let totalPages = 1;
// let hasSearched = false; // Track if a search has been performed
// let stallingSSSE = null; // Server-Sent Events connection for stalling messages

// // SSE global variables
// let eventSource = null;
// let resultsAccumulator = null;

// // DOM elements
// document.addEventListener('DOMContentLoaded', () => {
//     const searchInput = document.getElementById('searchInput');
//     const resultsDiv = document.getElementById('results');
//     const paginationDiv = document.getElementById('pagination');
//     const modal = document.getElementById('lawModal');
//     const modalTitle = document.getElementById('modalTitle');
//     const modalContent = document.getElementById('modalContent');
//     const closeModalBtn = document.getElementById('closeModal');
//     const loader = document.getElementById('loader');
//     const toast = document.getElementById('toast');
//     const toastIcon = document.getElementById('toastIcon');
//     const toastMessage = document.getElementById('toastMessage');
//     const stallingContainer = document.getElementById('stallingContainer');
//     const stallingMessage = document.getElementById('stallingMessage');

//     // Stalling messages that can be displayed while searching
//     const STALLING_MESSAGES = [
//         "Alright, let me get to work on this.",
//         "I'm parsing your request...",
//         "Searching the legal database for relevant information...",
//         "Analyzing your query...",
//         "Looking through American law documents...",
//         "Converting your question to structured query language...",
//         "Working on retrieving the most relevant legal information...",
//         "Processing your request...",
//         "Examining the database to find matching legal documents...",
//         "Searching through legal citations that match your query..."
//     ];

//     // Show/hide loading indicator
//     function setLoading(isLoading) {
//         loader.style.display = isLoading ? 'block' : 'none';
//     }
    
//     // Show toast notification
//     function showToast(message, type = 'error') {
//         toastMessage.textContent = message;
        
//         if (type === 'error') {
//             toast.className = 'toast toast-error active';
//             toastIcon.className = 'fas fa-exclamation-circle text-red-500';
//         } else {
//             toast.className = 'toast toast-success active';
//             toastIcon.className = 'fas fa-check-circle text-green-500';
//         }
        
//         setTimeout(() => {
//             toast.classList.remove('active');
//         }, 3000);
//     }

//     // Start showing stalling messages
//     function startStallingMessages() {
//         // Close any existing SSE connection
//         if (stallingSSSE) {
//             stallingSSSE.close();
//         }

//         // Show the stalling container
//         stallingContainer.style.display = 'block';

//         // Initialize with first stalling message
//         stallingMessage.textContent = STALLING_MESSAGES[0];

//         // Setup manual rotation of stalling messages (since we're not using server-side SSE)
//         let messageIndex = 1;
//         const interval = setInterval(() => {
//             // Rotate through stalling messages
//             stallingMessage.textContent = STALLING_MESSAGES[messageIndex % STALLING_MESSAGES.length];
//             messageIndex++;
//         }, 3000);

//         // Store the interval ID in the stallingSSSE variable for cleanup
//         stallingSSSE = { 
//             close: () => {
//                 clearInterval(interval);
//                 stallingContainer.style.display = 'none';
//             }
//         };
//     }

//     // Stop showing stalling messages
//     function stopStallingMessages() {
//         if (stallingSSSE) {
//             stallingSSSE.close();
//             stallingSSSE = null;
//         }
//         stallingContainer.style.display = 'none';
//     }

//     // New method to use SSE for searching
//     function searchLawsSSE(query, page = 1, perPage = 20) {
//         // Set hasSearched flag to true
//         hasSearched = true;
        
//         currentQuery = query;
//         currentPage = page;
        
//         // Start showing stalling messages
//         startStallingMessages();
        
//         // Hide the regular loading indicator (we're using stalling messages instead)
//         setLoading(false);
        
//         resultsDiv.innerHTML = '';
        
//         // Close any existing EventSource connection
//         if (eventSource) {
//             eventSource.close();
//         }
        
//         // Initialize results accumulator
//         resultsAccumulator = {
//             results: [],
//             total: 0,
//             page: page,
//             per_page: 0,
//             total_pages: 0
//         };
        
//         // Create a new EventSource connection
//         const url = `/api/search/sse?q=${encodeURIComponent(query)}&page=${page}&per_page=${perPage}`;
//         eventSource = new EventSource(url);
        
//         // Handle the search_started event
//         eventSource.addEventListener('search_started', function(event) {
//             const data = JSON.parse(event.data);
//             console.log('Search started:', data);
//             // You could update your UI here to indicate the search has started
//         });
        
//         // Handle the results_update event
//         eventSource.addEventListener('results_update', function(event) {
//             const data = JSON.parse(event.data);
            
//             // Update our accumulator with the latest results
//             resultsAccumulator = data;
            
//             // Update the UI with the latest results
//             displayResults(data.results);
//             displayPagination(data.total_pages);
            
//             // Show the results and pagination containers
//             document.getElementById('results').style.display = 'block';
//             document.getElementById('pagination').style.display = 'flex';
            
//             // You could display an interim message here
//             if (data.results.length > 0) {
//                 showToast(`Found ${data.results.length} results so far...`, 'info');
//             }
//         });
        
//         // Handle the search_complete event
//         eventSource.addEventListener('search_complete', function(event) {
//             const data = JSON.parse(event.data);
//             console.log('Search completed:', data);
            
//             // Stop showing stalling messages
//             stopStallingMessages();
            
//             // Show final results message
//             if (resultsAccumulator.results.length === 0 && query) {
//                 showToast('No results found. Try different keywords.', 'error');
//             } else if (query) {
//                 showToast(`Found ${resultsAccumulator.total} results`, 'success');
//             }
            
//             // Close the connection
//             eventSource.close();
//             eventSource = null;
//         });
        
//         // Handle errors
//         eventSource.addEventListener('error', function(event) {
//             console.error('EventSource error:', event);
            
//             if (event.data) {
//                 const data = JSON.parse(event.data);
//                 showToast(`Error: ${data.message}`, 'error');
//             } else {
//                 showToast('An error occurred while searching. Please try again.', 'error');
//             }
            
//             // Stop showing stalling messages
//             stopStallingMessages();
            
//             // Close the connection
//             eventSource.close();
//             eventSource = null;
//         });
//     }

//     // Search on Enter key press - this is the main change
//     searchInput.addEventListener('keypress', (e) => {
//         if (e.key === 'Enter') {
//             const query = e.target.value.trim();
//             if (query) {
//                 searchLawsSSE(query);
//             }
//         }
//     });

//     // Add a cleanup function to close the EventSource when needed
//     function cleanupEventSource() {
//         if (eventSource) {
//             eventSource.close();
//             eventSource = null;
//         }
//     }

//     // Call this cleanup function when appropriate (e.g., when component unmounts or page unloads)
//     window.addEventListener('beforeunload', cleanupEventSource);

//     function displayResults(results) {
//         resultsDiv.innerHTML = '';
        
//         if (results.length === 0) {
//             resultsDiv.innerHTML = `
//                 <div class="neu-card result-card text-center opacity-0">
//                     <p class="text-gray-600">No results found. Try different keywords.</p>
//                 </div>
//             `;

//             // Animate the single "no results" card
//             setTimeout(() => {
//                 const card = resultsDiv.querySelector('.neu-card');
//                 card.classList.remove('opacity-0');
//                 card.classList.add('fade-in');
//             }, 100);
            
//             return;
//         }

//         // Create all cards but make them initially invisible
//         results.forEach((law, index) => {
//             const lawCard = document.createElement('div');

//             lawCard.className = 'neu-card result-card opacity-0';
//             lawCard.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
//             lawCard.style.transform = 'translateY(20px)';

//             // <p class="html-content">${law.html}</p>
//             lawCard.innerHTML = `
//                 <h3 class="result-title">${law.title}</h3>
//                 <div class="result-meta">
//                     <span class="font-medium">${law.place_name}, ${law.state_name}</span> • 
//                     <span>${law.chapter}</span>
//                 </div>
//                 <div class="text-text-light">${law.bluebook_citation}</div>
//                 <div class="result-footer">
//                     <button class="view-law-btn btn btn-primary" data-id="${law.cid}">
//                         View Full Text <i class="fas fa-arrow-right ml-1"></i>
//                     </button>
//                 </div>
//             `;

//             resultsDiv.appendChild(lawCard);

//             // Add event listener to the button
//             const viewBtn = lawCard.querySelector('.view-law-btn');
//             viewBtn.addEventListener('click', () => viewLaw(law.cid));
//             let delay = 100 + (index * 100); // Staggered delay for each card

//             // Staggered animation for each card
//             setTimeout(() => {
//                 lawCard.classList.remove('opacity-0');
//                 lawCard.style.opacity = '1';
//                 lawCard.style.transform = 'translateY(0)';
//             }, delay); // 150ms delay between each card animation
//         });
//     }

//     function displayPagination(total) {
//         totalPages = total;
//         paginationDiv.innerHTML = '';
        
//         if (total <= 1) return;
        
//         // Previous button
//         if (currentPage > 1) {
//             const prevButton = createPaginationButton('Previous', currentPage - 1);
//             paginationDiv.appendChild(prevButton);
//         }
        
//         // Page numbers
//         const startPage = Math.max(1, currentPage - 2);
//         const endPage = Math.min(total, startPage + 4);
        
//         for (let i = startPage; i <= endPage; i++) {
//             const pageButton = createPaginationButton(i.toString(), i, i === currentPage);
//             paginationDiv.appendChild(pageButton);
//         }
        
//         // Next button
//         if (currentPage < total) {
//             const nextButton = createPaginationButton('Next', currentPage + 1);
//             paginationDiv.appendChild(nextButton);
//         }
//     }

//     function createPaginationButton(text, page, isActive = false) {
//         const button = document.createElement('button');
//         button.className = `page-btn ${isActive ? 'active' : ''}`;
//         button.textContent = text;
//         button.setAttribute('aria-label', `Page ${text}`);
        
//         button.addEventListener('click', () => searchLawsSSE(currentQuery, page));
//         return button;
//     }

//     async function viewLaw(lawCid) {
//         try {
//             // Start stalling messages for law view as well
//             startStallingMessages();
            
//             const response = await fetch(`/api/law/${lawCid}`);
//             if (!response.ok) {
//                 throw new Error('Network response was not ok');
//             }
            
//             const law = await response.json();
            
//             // Stop stalling messages
//             stopStallingMessages();
            
//             modalTitle.textContent = law.title;
//             modalContent.innerHTML = `
//                 <div class="mb-4">
//                     <div class="text-sm text-gray-600">
//                         <span class="font-medium">${law.place_name}, ${law.state_name}</span> • 
//                         <span>${law.chapter}</span>
//                     </div>
//                 </div>
//                 <div id="law-chunk" class="prose max-w-none">
//                     ${law.html.split('\n').map(para => `<p class="mb-4">${para}</p>`).join('')}
//                 </div>
//                 <div class="text-sm text-gray-500 mt-1">Bluebook Citation: ${law.bluebook_citation}</div>
//             `;
            
//             // Show modal with animation
//             modal.classList.add('active');
            
//             // Add accessibility focus
//             closeModalBtn.focus();
            
//             // Add keyboard support
//             document.addEventListener('keydown', handleEscapeKey);
//         } catch (error) {
//             console.error('Error fetching law details:', error);
//             showToast('An error occurred while loading the law details.', 'error');
//             stopStallingMessages();
//         }
//     }
    
//     function closeModal() {
//         modal.classList.remove('active');
//         document.removeEventListener('keydown', handleEscapeKey);
//     }
    
//     function handleEscapeKey(e) {
//         if (e.key === 'Escape') {
//             closeModal();
//         }
//     }

//     // Modal close event listeners
//     closeModalBtn.addEventListener('click', closeModal);
    
//     // Click outside modal to close
//     modal.addEventListener('click', (e) => {
//         if (e.target === modal) {
//             closeModal();
//         }
//     });

//     // Hide results and stalling container initially
//     document.getElementById('results').style.display = 'none';
//     document.getElementById('pagination').style.display = 'none';
//     stallingContainer.style.display = 'none';
// });


// Global variables
let currentPage = 1;
let currentQuery = '';
let totalPages = 1;
let hasSearched = false;
let stallingSSSE = null;

// SSE global variables
let eventSource = null;
let resultsAccumulator = null;

// LLM mode variables
let isLLMMode = false;
let llmConversationHistory = [];

// DOM elements
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('results');
    const paginationDiv = document.getElementById('pagination');
    const modal = document.getElementById('lawModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const closeModalBtn = document.getElementById('closeModal');
    const loader = document.getElementById('loader');
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');
    const stallingContainer = document.getElementById('stallingContainer');
    const stallingMessage = document.getElementById('stallingMessage');

    // Stalling messages
    const STALLING_MESSAGES = [
        "Alright, let me get to work on this.",
        "I'm parsing your request...",
        "Searching the legal database for relevant information...",
        "Analyzing your query...",
        "Looking through American law documents...",
        "Converting your question to structured query language...",
        "Working on retrieving the most relevant legal information...",
        "Processing your request...",
        "Examining the database to find matching legal documents...",
        "Searching through legal citations that match your query..."
    ];

    const LLM_STALLING_MESSAGES = [
        "Thinking about your question...",
        "Processing your request...",
        "Analyzing the context...",
        "Formulating a response...",
        "Considering the best way to help you..."
    ];

    function setLoading(isLoading) {
        loader.style.display = isLoading ? 'block' : 'none';
    }
    
    function showToast(message, type = 'error') {
        toastMessage.textContent = message;
        
        if (type === 'error') {
            toast.className = 'toast toast-error active';
            toastIcon.className = 'fas fa-exclamation-circle text-red-500';
        } else if (type === 'success') {
            toast.className = 'toast toast-success active';
            toastIcon.className = 'fas fa-check-circle text-green-500';
        } else {
            toast.className = 'toast toast-info active';
            toastIcon.className = 'fas fa-info-circle text-blue-500';
        }
        
        setTimeout(() => {
            toast.classList.remove('active');
        }, 3000);
    }

    function startStallingMessages(useLLMMessages = false) {
        if (stallingSSSE) {
            stallingSSSE.close();
        }

        stallingContainer.style.display = 'block';
        
        const messages = useLLMMessages ? LLM_STALLING_MESSAGES : STALLING_MESSAGES;
        stallingMessage.textContent = messages[0];

        let messageIndex = 1;
        const interval = setInterval(() => {
            stallingMessage.textContent = messages[messageIndex % messages.length];
            messageIndex++;
        }, 3000);

        stallingSSSE = { 
            close: () => {
                clearInterval(interval);
                stallingContainer.style.display = 'none';
            }
        };
    }

    function stopStallingMessages() {
        if (stallingSSSE) {
            stallingSSSE.close();
            stallingSSSE = null;
        }
        stallingContainer.style.display = 'none';
    }

    // Add these updated functions to your JavaScript
    function activateLLMMode() {
        isLLMMode = true;
        llmConversationHistory = [];
        
        // Update UI
        searchInput.placeholder = "Chat with the AI about laws... (type 'exit llm' to return to search)";
        searchInput.classList.add('llm-mode-active');
        
        // Apply layout changes for LLM mode
        const container = document.querySelector('.container');
        const searchContainer = document.querySelector('.search-container');
        
        // Option 1: Fixed input at bottom (recommended)
        container.classList.add('llm-active');
        searchContainer.classList.add('llm-fixed');
        resultsDiv.classList.add('llm-scroll');
        
        // Option 2: Sticky input at top (uncomment if you prefer this)
        // searchContainer.classList.add('llm-sticky');
        
        // Make results visible
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '';
        paginationDiv.style.display = 'none';
        paginationDiv.innerHTML = '';
        
        // Add body class for any global styles
        document.body.classList.add('llm-mode-active');
        
        // Display welcome message
        displayLLMMessage("Hello! I'm now in conversation mode. I can help you understand laws, answer legal questions, and have a conversation about legal topics. How can I assist you?", 'assistant');
        
        showToast('LLM Mode Activated - You can now have a conversation!', 'success');
    }

    function deactivateLLMMode() {
        isLLMMode = false;
        llmConversationHistory = [];
        
        // Reset UI
        searchInput.placeholder = "What laws would you like to find?";
        searchInput.classList.remove('llm-mode-active');
        
        // Remove layout classes
        const container = document.querySelector('.container');
        const searchContainer = document.querySelector('.search-container');
        
        container.classList.remove('llm-active');
        searchContainer.classList.remove('llm-fixed');
        searchContainer.classList.remove('llm-sticky');
        resultsDiv.classList.remove('llm-scroll');
        
        // Remove body class
        document.body.classList.remove('llm-mode-active');
        
        // Clear conversation
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        paginationDiv.innerHTML = '';
        
        showToast('Returned to Search Mode', 'info');
    }

    // Update llmConversationSSE to auto-scroll
    function llmConversationSSE(userMessage) {
        hasSearched = true;
        
        // Display user message
        displayLLMMessage(userMessage, 'user');
        
        // Add to conversation history
        llmConversationHistory.push({ role: 'user', content: userMessage });
        
        // Start stalling messages
        startStallingMessages(true);
        
        // Close any existing EventSource connection
        if (eventSource) {
            eventSource.close();
        }
        
        // Make sure results div is visible
        resultsDiv.style.display = 'block';
        paginationDiv.style.display = 'none';
        
        // Create assistant message container for streaming
        const assistantMessageDiv = document.createElement('div');
        assistantMessageDiv.className = 'llm-message llm-assistant';
        assistantMessageDiv.style.opacity = '0';
        assistantMessageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-robot"></i>
                <span class="role-label">AI Assistant</span>
            </div>
            <div class="message-content"></div>
        `;
        resultsDiv.appendChild(assistantMessageDiv);
        
        // Animate in
        requestAnimationFrame(() => {
            assistantMessageDiv.style.transition = 'opacity 0.3s ease';
            assistantMessageDiv.style.opacity = '1';
        });
        
        const contentDiv = assistantMessageDiv.querySelector('.message-content');
        let fullResponse = '';
        
        // Create EventSource for streaming
        const url = `/api/llm/conversation?q=${encodeURIComponent(userMessage)}`;
        eventSource = new EventSource(url);
        
        eventSource.addEventListener('conversation_started', function(event) {
            const data = JSON.parse(event.data);
            console.log('Conversation started:', data);
            stopStallingMessages();
        });
        
        eventSource.addEventListener('token', function(event) {
            try {
                const data = JSON.parse(event.data);
                fullResponse = data.full_response || fullResponse + (data.token || '');
                
                // Update content
                contentDiv.textContent = fullResponse;
                
                // Smooth scroll to bottom of results
                resultsDiv.scrollTop = resultsDiv.scrollHeight;
            } catch (e) {
                console.error('Error processing token:', e);
            }
        });
        
        eventSource.addEventListener('conversation_complete', function(event) {
            const data = JSON.parse(event.data);
            console.log('Conversation complete:', data);
            
            // Make sure we have the final response
            if (data.full_response) {
                contentDiv.textContent = data.full_response;
            }
            
            // Add to conversation history
            llmConversationHistory.push({ role: 'assistant', content: fullResponse || data.full_response });
            
            // Final scroll to bottom
            resultsDiv.scrollTop = resultsDiv.scrollHeight;
            
            // Close connection
            eventSource.close();
            eventSource = null;
        });
        
        eventSource.onerror = function(event) {
            console.error('SSE error:', event);
            
            stopStallingMessages();
            
            contentDiv.textContent = 'An error occurred. Please try again.';
            showToast('An error occurred. Please try again.', 'error');
            
            eventSource.close();
            eventSource = null;
        };
    }

    // Update displayLLMMessage to auto-scroll
    function displayLLMMessage(message, role = 'assistant') {
        // Make sure results div is visible
        resultsDiv.style.display = 'block';
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `llm-message llm-${role}`;
        messageDiv.style.opacity = '0';
        
        const iconClass = role === 'user' ? 'fa-user' : 'fa-robot';
        const roleLabel = role === 'user' ? 'You' : 'AI Assistant';
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas ${iconClass}"></i>
                <span class="role-label">${roleLabel}</span>
            </div>
            <div class="message-content">${message}</div>
        `;
        
        resultsDiv.appendChild(messageDiv);
        
        // Animate in
        requestAnimationFrame(() => {
            messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            messageDiv.style.transform = 'translateY(0)';
            messageDiv.style.opacity = '1';
        });
        
        // Scroll to bottom smoothly
        setTimeout(() => {
            resultsDiv.scrollTop = resultsDiv.scrollHeight;
        }, 50);
    }

    function searchLawsSSE(query, page = 1, perPage = 20) {
        hasSearched = true;
        currentQuery = query;
        currentPage = page;
        
        startStallingMessages(false);
        setLoading(false);
        resultsDiv.innerHTML = '';
        
        if (eventSource) {
            eventSource.close();
        }
        
        resultsAccumulator = {
            results: [],
            total: 0,
            page: page,
            per_page: 0,
            total_pages: 0
        };
        
        const url = `/api/search/sse?q=${encodeURIComponent(query)}&page=${page}&per_page=${perPage}`;
        eventSource = new EventSource(url);
        
        eventSource.addEventListener('search_started', function(event) {
            const data = JSON.parse(event.data);
            console.log('Search started:', data);
        });
        
        eventSource.addEventListener('results_update', function(event) {
            const data = JSON.parse(event.data);
            resultsAccumulator = data;
            displayResults(data.results);
            displayPagination(data.total_pages);
            
            document.getElementById('results').style.display = 'block';
            document.getElementById('pagination').style.display = 'flex';
            
            if (data.results.length > 0) {
                showToast(`Found ${data.results.length} results so far...`, 'info');
            }
        });
        
        eventSource.addEventListener('search_complete', function(event) {
            const data = JSON.parse(event.data);
            console.log('Search completed:', data);
            
            stopStallingMessages();
            
            if (resultsAccumulator.results.length === 0 && query) {
                showToast('No results found. Try different keywords.', 'error');
            } else if (query) {
                showToast(`Found ${resultsAccumulator.total} results`, 'success');
            }
            
            eventSource.close();
            eventSource = null;
        });
        
        eventSource.addEventListener('error', function(event) {
            console.error('EventSource error:', event);
            
            if (event.data) {
                const data = JSON.parse(event.data);
                showToast(`Error: ${data.message}`, 'error');
            } else {
                showToast('An error occurred while searching. Please try again.', 'error');
            }
            
            stopStallingMessages();
            eventSource.close();
            eventSource = null;
        });
    }

    // Main search input handler
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (!query) return;
            
            // Check for LLM mode activation
            if (query.toLowerCase() === 'activate llm') {
                activateLLMMode();
                e.target.value = '';
                return;
            }
            
            // Check for LLM mode deactivation
            if (isLLMMode && query.toLowerCase() === 'exit llm') {
                deactivateLLMMode();
                e.target.value = '';
                return;
            }
            
            // Route to appropriate handler
            if (isLLMMode) {
                llmConversationSSE(query);
            } else {
                searchLawsSSE(query);
            }
            
            e.target.value = '';
        }
    });

    function cleanupEventSource() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }

    window.addEventListener('beforeunload', cleanupEventSource);

    function displayResults(results) {
        resultsDiv.innerHTML = '';
        
        if (results.length === 0) {
            resultsDiv.innerHTML = `
                <div class="neu-card result-card text-center opacity-0">
                    <p class="text-gray-600">No results found. Try different keywords.</p>
                </div>
            `;

            setTimeout(() => {
                const card = resultsDiv.querySelector('.neu-card');
                card.classList.remove('opacity-0');
                card.classList.add('fade-in');
            }, 100);
            
            return;
        }

        results.forEach((law, index) => {
            const lawCard = document.createElement('div');
            lawCard.className = 'neu-card result-card opacity-0';
            lawCard.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            lawCard.style.transform = 'translateY(20px)';

            lawCard.innerHTML = `
                <h3 class="result-title">${law.title}</h3>
                <div class="result-meta">
                    <span class="font-medium">${law.place_name}, ${law.state_name}</span> • 
                    <span>${law.chapter}</span>
                </div>
                <div class="text-text-light">${law.bluebook_citation}</div>
                <div class="result-footer">
                    <button class="view-law-btn btn btn-primary" data-id="${law.cid}">
                        View Full Text <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>
            `;

            resultsDiv.appendChild(lawCard);

            const viewBtn = lawCard.querySelector('.view-law-btn');
            viewBtn.addEventListener('click', () => viewLaw(law.cid));
            
            let delay = 100 + (index * 100);

            setTimeout(() => {
                lawCard.classList.remove('opacity-0');
                lawCard.style.opacity = '1';
                lawCard.style.transform = 'translateY(0)';
            }, delay);
        });
    }

    function displayPagination(total) {
        totalPages = total;
        paginationDiv.innerHTML = '';
        
        if (total <= 1) return;
        
        if (currentPage > 1) {
            const prevButton = createPaginationButton('Previous', currentPage - 1);
            paginationDiv.appendChild(prevButton);
        }
        
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(total, startPage + 4);
        
        for (let i = startPage; i <= endPage; i++) {
            const pageButton = createPaginationButton(i.toString(), i, i === currentPage);
            paginationDiv.appendChild(pageButton);
        }
        
        if (currentPage < total) {
            const nextButton = createPaginationButton('Next', currentPage + 1);
            paginationDiv.appendChild(nextButton);
        }
    }

    function createPaginationButton(text, page, isActive = false) {
        const button = document.createElement('button');
        button.className = `page-btn ${isActive ? 'active' : ''}`;
        button.textContent = text;
        button.setAttribute('aria-label', `Page ${text}`);
        
        button.addEventListener('click', () => searchLawsSSE(currentQuery, page));
        return button;
    }

    async function viewLaw(lawCid) {
        try {
            startStallingMessages();
            
            const response = await fetch(`/api/law/${lawCid}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const law = await response.json();
            
            stopStallingMessages();
            
            modalTitle.textContent = law.title;
            modalContent.innerHTML = `
                <div class="mb-4">
                    <div class="text-sm text-gray-600">
                        <span class="font-medium">${law.place_name}, ${law.state_name}</span> • 
                        <span>${law.chapter}</span>
                    </div>
                </div>
                <div id="law-chunk" class="prose max-w-none">
                    ${law.html.split('\n').map(para => `<p class="mb-4">${para}</p>`).join('')}
                </div>
                <div class="text-sm text-gray-500 mt-1">Bluebook Citation: ${law.bluebook_citation}</div>
            `;
            
            modal.classList.add('active');
            closeModalBtn.focus();
            document.addEventListener('keydown', handleEscapeKey);
        } catch (error) {
            console.error('Error fetching law details:', error);
            showToast('An error occurred while loading the law details.', 'error');
            stopStallingMessages();
        }
    }
    
    function closeModal() {
        modal.classList.remove('active');
        document.removeEventListener('keydown', handleEscapeKey);
    }
    
    function handleEscapeKey(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    }

    closeModalBtn.addEventListener('click', closeModal);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    document.getElementById('results').style.display = 'none';
    document.getElementById('pagination').style.display = 'none';
    stallingContainer.style.display = 'none';
});