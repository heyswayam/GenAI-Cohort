Your while loop function is mostly correct but can definitely be improved for token management and efficiency. Here are several optimization strategies:

## Current Issues:
1. **Unbounded token growth** - messages array grows indefinitely
2. **No token counting** - you're flying blind on costs
3. **No conversation summarization** - old context gets expensive

## Improved Approaches:

### Option 1: Simple Message Limit with Sliding Window
````python
def gpt_mini(msg):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=msg
    )
    return response.choices[0].message.content

def maintain_context_window(messages, max_messages=10):
    """Keep only recent messages + system prompt"""
    if len(messages) > max_messages:
        # Keep system prompt + last (max_messages-1) messages
        return [messages[0]] + messages[-(max_messages-1):]
    return messages

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    query = input("> ")
    if query.lower() == "stop":
        break
        
    messages.append({"role": "user", "content": query})
    
    # Maintain context window
    messages = maintain_context_window(messages, max_messages=10)
    
    response = gpt_mini(messages)
    print(f"🤖 Hitesh: {response}")
    messages.append({"role": "assistant", "content": response})
````

### Option 2: Smart Summarization Approach
````python
def summarize_conversation(messages):
    """Summarize old conversation to save tokens"""
    # Take messages to summarize (excluding system prompt and recent 4 messages)
    to_summarize = messages[1:-4]  # Skip system prompt and keep last 4
    
    if len(to_summarize) < 4:  # Not enough to summarize
        return messages
    
    # Create summarization prompt
    summary_messages = [
        {"role": "system", "content": "Summarize this conversation concisely, preserving key context and the persona's personality."},
        {"role": "user", "content": f"Conversation to summarize:\n{json.dumps(to_summarize, indent=2)}"}
    ]
    
    summary_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=summary_messages
    )
    
    summary = summary_response.choices[0].message.content
    
    # Return: system prompt + summary + recent messages
    return [
        messages[0],  # System prompt
        {"role": "system", "content": f"Previous conversation summary: {summary}"},
        *messages[-4:]  # Last 4 messages
    ]

def smart_context_management(messages, max_length=12):
    if len(messages) > max_length:
        return summarize_conversation(messages)
    return messages
````

### Option 3: Token-Based Management (Most Advanced)
````python
import tiktoken

def count_tokens(messages, model="gpt-4o-mini"):
    """Count tokens in messages"""
    encoding = tiktoken.encoding_for_model(model)
    token_count = 0
    
    for message in messages:
        # Count tokens for role and content
        token_count += len(encoding.encode(message["role"]))
        token_count += len(encoding.encode(message["content"]))
        token_count += 4  # Every message has some overhead
    
    return token_count

def manage_by_tokens(messages, max_tokens=3000):
    """Keep messages under token limit"""
    current_tokens = count_tokens(messages)
    
    if current_tokens <= max_tokens:
        return messages
    
    # Remove oldest messages (except system prompt) until under limit
    while current_tokens > max_tokens and len(messages) > 2:
        messages.pop(1)  # Remove oldest non-system message
        current_tokens = count_tokens(messages)
    
    return messages

# Usage in your loop:
while True:
    query = input("> ")
    if query.lower() == "stop":
        break
        
    messages.append({"role": "user", "content": query})
    
    # Token-based management
    messages = manage_by_tokens(messages, max_tokens=3000)
    
    response = gpt_mini(messages)
    print(f"🤖 Hitesh: {response}")
    messages.append({"role": "assistant", "content": response})
    
    # Optional: Show current token usage
    print(f"💰 Current tokens: {count_tokens(messages)}")
````

### Option 4: Hybrid Approach (Recommended)
````python
def optimal_context_management(messages, max_messages=15, max_tokens=4000):
    """Combine message count and token limits"""
    
    # First, check token limit
    current_tokens = count_tokens(messages)
    
    if current_tokens > max_tokens:
        # Summarize if too many tokens
        messages = summarize_conversation(messages)
    elif len(messages) > max_messages:
        # Simple sliding window if too many messages but tokens OK
        messages = maintain_context_window(messages, max_messages)
    
    return messages
````

## Best Practices:
1. **Always preserve system prompt** (index 0)
2. **Keep recent 3-4 messages** for immediate context
3. **Monitor token usage** to control costs
4. **Use summarization** for long conversations
5. **Add conversation memory** for important details

Choose the approach based on your needs:
- **Simple projects**: Option 1
- **Production apps**: Option 4
- **Cost-sensitive**: Option 3