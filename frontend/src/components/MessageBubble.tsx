import React from 'react';
import { Message } from '../../shared/types/conversation';
import { SourceChunk } from '../../shared/types/query';
import { User, Bot, FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';

type MessageBubbleProps = {
  message: Message;
  sources?: SourceChunk[];
  showSources?: boolean;
  onToggleSources?: () => void;
};

export default function MessageBubble({
  message,
  sources = [],
  showSources = false,
  onToggleSources,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const hasSources = sources.length > 0 && message.role === 'assistant';
  
  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm');
    } catch (error) {
      return '--:--';
    }
  };
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isUser ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'}`}>
            {isUser ? (
              <User className="w-5 h-5" />
            ) : (
              <Bot className="w-5 h-5" />
            )}
          </div>
        </div>
        
        {/* Message content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`px-4 py-3 rounded-2xl ${isUser ? 'rounded-tr-none bg-blue-500 text-white' : 'rounded-tl-none bg-gray-100 text-gray-900'}`}
          >
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
            
            {/* Sources toggle */}
            {hasSources && (
              <button
                onClick={onToggleSources}
                className={`mt-2 flex items-center text-sm ${isUser ? 'text-blue-200 hover:text-blue-100' : 'text-gray-500 hover:text-gray-700'}`}
              >
                {showSources ? (
                  <>
                    <ChevronUp className="w-4 h-4 mr-1" />
                    Hide sources ({sources.length})
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-4 h-4 mr-1" />
                    Show sources ({sources.length})
                  </>
                )}
              </button>
            )}
          </div>
          
          {/* Timestamp */}
          <div className="mt-1 text-xs text-gray-500 px-1">
            {formatTimestamp(message.timestamp)}
          </div>
          
          {/* Sources panel */}
          {hasSources && showSources && (
            <div className="mt-3 w-full max-w-md">
              <div className="text-xs font-medium text-gray-500 mb-2">
                Sources used for this response:
              </div>
              <div className="space-y-2">
                {sources.map((source, index) => (
                  <div
                    key={`${source.chunk_id}-${index}`}
                    className="bg-white border border-gray-200 rounded-lg p-3 text-sm"
                  >
                    <div className="flex items-start justify-between mb-1">
                      <div className="flex items-center text-gray-700">
                        <FileText className="w-3 h-3 mr-1 flex-shrink-0" />
                        <span className="font-medium truncate">
                          {source.document_filename}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 ml-2">
                        {Math.round(source.score * 100)}% match
                      </div>
                    </div>
                    <div className="text-gray-600 mt-2 line-clamp-3">
                      {source.content}
                    </div>
                    <div className="text-xs text-gray-400 mt-2 flex justify-between items-center">
                      <span>Chunk ID: {source.chunk_id.substring(0, 8)}...</span>
                      <button
                        className="text-blue-500 hover:text-blue-700 flex items-center"
                        onClick={() => {
                          // In a real app, this would navigate to the document
                          console.log('View document:', source.document_id);
                        }}
                      >
                        <ExternalLink className="w-3 h-3 mr-1" />
                        View document
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
