import { useState } from 'react';
import './App.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false); // New loading state

  const handleSend = async () => {
    if (input.trim()) {
      const newMessages = [...messages, { text: input, sender: 'user' }];
      setMessages(newMessages);
      setInput('');
      setIsLoading(true); // Set loading to true

      try {
        const response = await fetch('http://localhost:8000/handle-request', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ prompt: input }),
        });
        const data = await response.json();
        
        let agentMessageContent;
        if (data.download_link) {
          agentMessageContent = (
            <>
              Your manual is ready! Download it{' '}
              <a href={`http://localhost:8000${data.download_link}`} target="_blank" rel="noopener noreferrer">
                here
              </a>
              .
            </>
          );
        } else if (data.response) {
          if (typeof data.response === 'object' && data.response !== null && 'error' in data.response) {
            agentMessageContent = `Error: ${data.response.error}`;
          } else {
            agentMessageContent = data.response;
          }
        } else {
          agentMessageContent = 'Error: Unexpected response from agent.';
        }

        setMessages([...newMessages, { text: agentMessageContent, sender: 'agent' }]);
      } catch (error) {
        console.error('Error fetching from API:', error);
        setMessages([...newMessages, { text: 'Error: Could not connect to the agent.', sender: 'agent' }]);
      } finally {
        setIsLoading(false); // Set loading to false regardless of success or error
      }
    }
  };

  return (
    <div className="chat-container">
      <div className="message-list">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
          </div>
        ))}
        {isLoading && (
          <div className="message agent">
            Processing...
          </div>
        )}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your message..."
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}

export default App;