import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, FileText, AlertCircle } from 'lucide-react';
import { Message } from '../../shared/types/conversation';
import { QueryRequest, QueryResponse, SourceChunk } from '../../shared/types/query';
import { sendQuery } from '../api/query';
import { useAuth } from '../hooks/useAuth';
import { format } from 'date-fns';

type ChatWindowProps = {
  conversationId: string;
  conversationTitle: string;
  initialMessages?: Message[];
  onNewMessage?: (message: Message) => void;
  onError?: (error: string) => void;
};

export default function ChatWindow({
  conversationId,
  conversationTitle,
  initialMessages = [],
  onNewMessage,
  onError,
}: ChatWindowProps) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Update messages when initialMessages prop changes
  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || !token || isLoading) return;

    const userMessage = inputText.trim();
    setInputText('');
    setIsLoading(true);

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, tempUserMessage]);
    onNewMessage?.(tempUserMessage);

    try {
      const queryRequest: QueryRequest = {
        conversation_id: conversationId,
        message: userMessage,
        include_sources: true,
      };

      const response = await sendQuery(queryRequest, token);
      setLastResponse(response);

      // Create assistant message from response
      const assistantMessage: Message = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        metadata: response.cached ? 'cached' : undefined,
      };

      // Replace temp message with real message
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== tempUserMessage.id);
        return [...filtered, assistantMessage];
      });
      
      onNewMessage?.(assistantMessage);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      onError?.(errorMessage);
      
      // Remove temp message on error
      setMessages(prev => prev.filter(msg => msg.id !== tempUserMessage.id));
      
      // Restore input text
      setInputText(userMessage);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const formatMessageTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm');
    } catch {
      return '--:--';
    }
  };

  const renderMessageContent = (content: string) => {
    return content.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < content.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const renderSources = () => {
    if (!lastResponse?.sources || lastResponse.sources.length === 0) {
      return null;
    }

    return (
      <div className="mt-4 border-t border-gray-200 pt-4">
        <div 
          className="flex items-center justify-between cursor-pointer text-sm font-medium text-gray-700"
          onClick={() => setShowSources(!showSources)}
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>Sources ({lastResponse.sources.length})</span>
            {lastResponse.cached && (
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                Cached
              </span>
            )}
          </div>
          <span className="text-gray-500">
            {showSources ? 'Hide' : 'Show'}
          </span>
        </div>
        
        {showSources && (
          <div className="mt-3 space-y-3">
            {lastResponse.sources.map((source: SourceChunk, index: number) => (
              <div 
                key={source.chunk_id}
                className="bg-gray-50 rounded-lg p-3 border border-gray-200"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                      #{index + 1}
                    </span>
                    <span className="text-xs font-medium text-gray-600 truncate">
                      {source.document_filename}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    Score: {source.score.toFixed(3)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 line-clamp-3">
                  {source.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">{conversationTitle}</h2>
            <p className="text-sm text-gray-500">
              {messages.length} message{messages.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isLoading && (
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500">
            <Bot className="w-16 h-16 mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">Start a conversation</h3>
            <p className="text-center text-gray-500 max-w-md">
              Ask questions about your documents. The AI will search through your uploaded files to provide relevant answers.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <div 
                key={message.id}
                className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' 
                    ? 'bg-blue-100 text-blue-600' 
                    : 'bg-green-100 text-green-600'
                }`}>
                  {message.role === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex-1 max-w-3xl ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div className={`inline-block px-4 py-3 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}>
                    <div className="whitespace-pre-wrap break-words">
                      {renderMessageContent(message.content)}
                    </div>
                  </div>
                  
                  {/* Message Metadata */}
                  <div className={`mt-2 text-xs text-gray-500 flex items-center gap-2 ${
                    message.role === 'user' ? 'justify-end' : ''
                  }`}>
                    <span>{formatMessageTime(message.timestamp)}</span>
                    {message.metadata === 'cached' && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                        Cached
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Sources section for last response */}
            {lastResponse && renderSources()}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-gray-50 rounded-b-lg">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message here..."
            disabled={isLoading || !token}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none resize-none min-h-[60px] max-h-[120px] disabled:bg-gray-100 disabled:cursor-not-allowed"
            rows={1}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isLoading || !token}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
        
        {/* Input hints */}
        <div className="mt-2 text-xs text-gray-500 flex justify-between">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>{inputText.length}/5000</span>
        </div>
      </div>
    </div>
  );
}
