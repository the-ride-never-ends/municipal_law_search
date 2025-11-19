# LLM Mode Implementation Guide

## Overview
This implementation adds an LLM conversation mode to your American Law Search application that can be activated via the keyphrase "activate llm" in the search bar.

## Features
- Keyphrase activation: Type "activate llm" to switch to conversation mode
- Exit phrase: Type "exit llm" to return to search mode
- Streaming responses: LLM responses stream token-by-token via SSE
- Conversation history: Maintains context across messages
- Visual distinction: Different styling for user vs assistant messages
- Smooth animations: Messages slide in smoothly

## Files Modified/Created

### 1. Backend (app.py)
Add the following to your existing `app.py`:

**New Route:**
```python
LLM_CONVERSATION = "/api/llm/conversation"
```

**New Methods:**
- `llm_conversation_sse()`: Handles streaming LLM responses
- `clear_llm_conversation()`: Clears conversation history
- Updated `get_mappings` and `post_mappings` properties
- Updated `make_app()` to register POST routes

**Key Changes:**
1. Added conversation history storage in `temp_storage`
2. Implemented streaming response via SSE
3. Added conversation context management

### 2. Frontend JavaScript (index.js)
Replace `/src/static/js/index/index.js` with the new version.

**New Features:**
- `isLLMMode` flag to track current mode
- `activateLLMMode()`: Switches to conversation mode
- `deactivateLLMMode()`: Returns to search mode
- `llmConversationSSE()`: Handles LLM streaming
- `displayLLMMessage()`: Renders conversation messages
- Updated search input handler to detect keyphrases

**Key Variables:**
- `llmConversationHistory[]`: Stores conversation context
- `LLM_STALLING_MESSAGES[]`: Messages shown during LLM processing

### 3. CSS Styling (llm-mode.css)
Add this new CSS file to your project.

**Styles Include:**
- `.llm-mode-active`: Input styling when LLM mode is active
- `.llm-message`: Base message container
- `.llm-user` / `.llm-assistant`: Different styles for each role
- `.message-header` / `.message-content`: Message structure
- Animations: Slide-in, typing indicator, pulse effect
- Responsive design for mobile

## Installation Steps

### Step 1: Update Backend

Add the code from `app_llm_mode.py` to your existing `/home/kylerose1946/american_law_search/app/app.py`:

1. Add the new route to the `Routes` enum
2. Add the two new methods (`llm_conversation_sse` and `clear_llm_conversation`)
3. Update the `get_mappings` property
4. Update the `post_mappings` property
5. Update the `make_app()` method to register POST routes

### Step 2: Update Frontend JavaScript

Replace the contents of `/home/kylerose1946/american_law_search/src/static/js/index/index.js` with the code from `index_with_llm.js`

### Step 3: Add CSS

1. Create a new file: `/home/kylerose1946/american_law_search/src/static/css/llm-mode.css`
2. Copy the contents from the provided `llm-mode.css` file
3. Add the following line to `/home/kylerose1946/american_law_search/src/templates/index.html` in the `<head>` section:

```html
<link href="/src/css/llm-mode.css" rel="stylesheet">
```

### Step 4: Update LLM Interface

Ensure your `llm.py` file has a `stream_response()` method that yields tokens. Example:

```python
async def stream_response(self, query: str, conversation_history: list) -> AsyncGenerator[str, None]:
    """
    Stream LLM response token by token.
    
    Args:
        query: User's current message
        conversation_history: List of previous messages
        
    Yields:
        str: Individual tokens or chunks of the response
    """
    # Your LLM streaming implementation here
    # Example:
    async for chunk in your_llm_client.stream(query, history=conversation_history):
        yield chunk
```

## Usage

### Activating LLM Mode
1. Type "activate llm" in the search bar
2. Press Enter
3. The search bar will change color and update its placeholder
4. A welcome message from the AI will appear

### Using LLM Mode
1. Type your question or message
2. Press Enter
3. Your message appears on the right (purple gradient)
4. AI response streams in on the left (white background)
5. Continue the conversation naturally

### Exiting LLM Mode
1. Type "exit llm" in the search bar
2. Press Enter
3. Returns to normal search mode
4. Conversation history is cleared

## API Endpoints

### GET `/api/llm/conversation`
Streams LLM responses via Server-Sent Events

**Query Parameters:**
- `q` (string, required): User's message
- `client_id` (string, optional): Client identifier for history

**SSE Events:**
- `conversation_started`: Processing has begun
- `token`: Each chunk of the response (includes `token` and `full_response`)
- `conversation_complete`: Response generation finished
- `error`: An error occurred

**Example:**
```javascript
const eventSource = new EventSource('/api/llm/conversation?q=Tell me about zoning laws');
eventSource.addEventListener('token', (event) => {
    const data = JSON.parse(event.data);
    console.log(data.token); // Current token
    console.log(data.full_response); // Full response so far
});
```

### POST `/api/llm/clear`
Clears conversation history for a client

**Query Parameters:**
- `client_id` (string, optional): Client identifier

**Response:**
```json
{
    "status": "success",
    "message": "Conversation history cleared"
}
```

## Customization

### Stalling Messages
Modify `LLM_STALLING_MESSAGES` array in the JavaScript to change messages shown during processing:

```javascript
const LLM_STALLING_MESSAGES = [
    "Thinking about your question...",
    "Your custom message here...",
    // Add more messages
];
```

### Message Styling
Edit `llm-mode.css` to change:
- Colors: Modify gradient values in `.llm-user`
- Animations: Adjust `@keyframes slideIn` timing
- Layout: Change margins in `.llm-message`

### Activation Keyphrase
Change the activation keyphrase in the JavaScript:

```javascript
// Change "activate llm" to your preferred phrase
if (query.toLowerCase() === 'your keyphrase here') {
    activateLLMMode();
    // ...
}
```

## Testing

### Test Activation
1. Open the application in a browser
2. Type "activate llm" and press Enter
3. Verify toast notification appears
4. Verify search bar changes color
5. Verify welcome message displays

### Test Conversation
1. Activate LLM mode
2. Type a question and press Enter
3. Verify your message appears on the right
4. Verify AI response streams in on the left
5. Send another message to test conversation history

### Test Deactivation
1. In LLM mode, type "exit llm" and press Enter
2. Verify toast notification appears
3. Verify search bar returns to normal
4. Verify conversation is cleared

## Troubleshooting

### LLM responses not streaming
- Check that `llm.stream_response()` is properly implemented
- Verify the `/api/llm/conversation` endpoint is registered
- Check browser console for errors

### Messages not displaying
- Verify `llm-mode.css` is loaded in the HTML
- Check browser console for JavaScript errors
- Verify `resultsDiv` element exists

### Conversation history not maintained
- Check `temp_storage["llm_conversations"]` is being populated
- Verify `client_id` is being passed correctly
- Check backend logs for errors

### Mode not activating
- Verify keyphrase is exactly "activate llm" (case-insensitive)
- Check that event listener is attached to search input
- Look for JavaScript errors in console

## Performance Considerations

- Conversation history grows with each message - consider implementing a max history limit
- SSE connections should be properly closed when switching modes
- Consider adding a "Clear History" button for long conversations
- Monitor memory usage for long-running conversations

## Security Notes

- Sanitize user input before displaying
- Implement rate limiting on the LLM endpoint
- Consider adding authentication for conversation history
- Validate and escape HTML in LLM responses to prevent XSS

## Future Enhancements

Potential features to add:
- Export conversation as PDF/text
- Save conversations to permanent storage
- Share conversation via link
- Voice input/output for conversations
- Code syntax highlighting in responses
- Markdown rendering support
- Conversation branching/forking