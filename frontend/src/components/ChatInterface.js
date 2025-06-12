import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  IconButton,
  CircularProgress,
  Divider,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';
import { userApi } from '../services/api';

const ChatInterface = ({ userId, sessionId, setSessionId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat history when component mounts or sessionId changes
  useEffect(() => {
    if (userId && sessionId) {
      loadChatHistory();
    }
  }, [userId, sessionId]);

  const loadChatHistory = async () => {
    try {
      setLoading(true);
      const response = await userApi.getHistory(userId, sessionId);
      if (response.data && response.data.messages) {
        setMessages(response.data.messages);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await userApi.submitQuery(input, userId, sessionId);
      
      // If no sessionId was provided, use the one from the response
      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      // Add assistant response to chat
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          sources: response.data.sources,
          confidence: response.data.confidence,
          needs_escalation: response.data.needs_escalation,
          escalation_reason: response.data.escalation_reason,
        },
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message to chat
      const errorMessage = {
        role: 'system',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      
      recorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await handleVoiceSubmit(audioBlob);
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      setRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && recording) {
      mediaRecorder.stop();
      setRecording(false);
      // Stop all audio tracks
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleVoiceSubmit = async (audioBlob) => {
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      formData.append('user_id', userId);
      if (sessionId) {
        formData.append('session_id', sessionId);
      }
      
      // Add processing message to chat
      const processingMessage = {
        role: 'system',
        content: 'Processing voice input...',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, processingMessage]);
      
      const response = await userApi.uploadVoice(formData);
      
      // If no sessionId was provided, use the one from the response
      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id);
      }
      
      // Remove processing message
      setMessages((prev) => prev.filter(msg => msg.content !== 'Processing voice input...'));
      
      // Add transcription and response to chat
      const userMessage = {
        role: 'user',
        content: response.data.transcription,
        timestamp: new Date().toISOString(),
        metadata: {
          is_voice: true,
        },
      };
      
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          sources: response.data.sources,
          confidence: response.data.confidence,
          needs_escalation: response.data.needs_escalation,
          escalation_reason: response.data.escalation_reason,
        },
      };
      
      setMessages((prev) => [...prev, userMessage, assistantMessage]);
    } catch (error) {
      console.error('Error processing voice input:', error);
      // Add error message to chat
      const errorMessage = {
        role: 'system',
        content: 'Sorry, there was an error processing your voice input.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev.filter(msg => msg.content !== 'Processing voice input...'), errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '80vh' }}>
      {/* Chat messages */}
      <Paper
        elevation={3}
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          mb: 2,
          bgcolor: '#f5f5f5',
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Typography variant="body1" color="textSecondary">
              Start a conversation with FinMate
            </Typography>
          </Box>
        ) : (
          messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: '80%',
                  bgcolor: message.role === 'user' ? '#e3f2fd' : message.role === 'system' ? '#ffebee' : '#fff',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body1">{message.content}</Typography>
                
                {/* Show sources if available */}
                {message.metadata?.sources && message.metadata.sources.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="caption" color="textSecondary">
                      Sources: {message.metadata.sources.join(', ')}
                    </Typography>
                  </Box>
                )}
                
                {/* Show escalation info if needed */}
                {message.metadata?.needs_escalation && (
                  <Box sx={{ mt: 1 }}>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="caption" color="error">
                      This query has been escalated to a human operator.
                    </Typography>
                  </Box>
                )}
              </Paper>
              
              <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5 }}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
            </Box>
          ))
        )}
        <div ref={messagesEndRef} />
      </Paper>

      {/* Input area */}
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading || recording}
          multiline
          maxRows={3}
          sx={{ mr: 1 }}
        />
        
        {/* Voice recording button */}
        <IconButton
          color={recording ? 'error' : 'primary'}
          onClick={recording ? stopRecording : startRecording}
          disabled={loading}
        >
          {recording ? <StopIcon /> : <MicIcon />}
        </IconButton>
        
        {/* Send button */}
        <Button
          variant="contained"
          color="primary"
          endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          onClick={handleSendMessage}
          disabled={!input.trim() || loading || recording}
          sx={{ ml: 1 }}
        >
          Send
        </Button>
      </Box>
    </Box>
  );
};

export default ChatInterface; 