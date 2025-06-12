import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Button,
  TextField,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { adminApi } from '../services/api';

const AdminPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [textTitle, setTextTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [knowledgeItems, setKnowledgeItems] = useState([]);
  const [escalations, setEscalations] = useState([]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setSuccess(false);
    setError(null);
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setSuccess(false);
    setError(null);
  };

  const handleTextChange = (event) => {
    setText(event.target.value);
    setSuccess(false);
    setError(null);
  };

  const handleTitleChange = (event) => {
    setTextTitle(event.target.value);
    setSuccess(false);
    setError(null);
  };

  const handleFileUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      await adminApi.uploadDocument(formData);
      setSuccess(true);
      setFile(null);
      // Refresh knowledge items
      fetchKnowledgeItems();
    } catch (error) {
      console.error('Error uploading file:', error);
      setError('Failed to upload file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTextUpload = async () => {
    if (!text || !textTitle) {
      setError('Please provide both title and content');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('title', textTitle);
      formData.append('content', text);
      
      await adminApi.uploadText(formData);
      setSuccess(true);
      setText('');
      setTextTitle('');
      // Refresh knowledge items
      fetchKnowledgeItems();
    } catch (error) {
      console.error('Error uploading text:', error);
      setError('Failed to upload text. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchKnowledgeItems = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getKnowledge();
      if (response.data && response.data.items) {
        setKnowledgeItems(response.data.items);
      }
    } catch (error) {
      console.error('Error fetching knowledge items:', error);
      setError('Failed to fetch knowledge items');
    } finally {
      setLoading(false);
    }
  };

  const fetchEscalations = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getEscalations();
      if (response.data && response.data.escalations) {
        setEscalations(response.data.escalations);
      }
    } catch (error) {
      console.error('Error fetching escalations:', error);
      setError('Failed to fetch escalations');
    } finally {
      setLoading(false);
    }
  };

  const handleResolveEscalation = async (escalationId, resolution, userId, sessionId) => {
    try {
      setLoading(true);
      await adminApi.resolveEscalation(escalationId, resolution, userId, sessionId);
      // Refresh escalations
      fetchEscalations();
    } catch (error) {
      console.error('Error resolving escalation:', error);
      setError('Failed to resolve escalation');
    } finally {
      setLoading(false);
    }
  };

  // Load data when tab changes
  React.useEffect(() => {
    if (tabValue === 1) {
      fetchKnowledgeItems();
    } else if (tabValue === 2) {
      fetchEscalations();
    }
  }, [tabValue]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          FinMate Admin Panel
        </Typography>
        
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
          <Tab label="Upload Content" />
          <Tab label="Knowledge Base" />
          <Tab label="Escalations" />
        </Tabs>

        {/* Upload Content Tab */}
        {tabValue === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Upload Document
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<UploadFileIcon />}
                >
                  Select File
                  <input
                    type="file"
                    hidden
                    onChange={handleFileChange}
                  />
                </Button>
                <Typography variant="body1" sx={{ ml: 2 }}>
                  {file ? file.name : 'No file selected'}
                </Typography>
              </Box>
              <Button
                variant="contained"
                color="primary"
                onClick={handleFileUpload}
                disabled={!file || loading}
                sx={{ mr: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Upload Document'}
              </Button>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Add Text Content
              </Typography>
              <TextField
                fullWidth
                label="Title"
                value={textTitle}
                onChange={handleTitleChange}
                margin="normal"
                variant="outlined"
              />
              <TextField
                fullWidth
                label="Content"
                value={text}
                onChange={handleTextChange}
                margin="normal"
                variant="outlined"
                multiline
                rows={6}
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleTextUpload}
                disabled={!text || !textTitle || loading}
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Add Text Content'}
              </Button>
            </Grid>

            {success && (
              <Grid item xs={12}>
                <Alert severity="success" sx={{ mt: 2 }}>
                  Content uploaded successfully!
                </Alert>
              </Grid>
            )}

            {error && (
              <Grid item xs={12}>
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              </Grid>
            )}
          </Grid>
        )}

        {/* Knowledge Base Tab */}
        {tabValue === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Knowledge Base Items
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                <CircularProgress />
              </Box>
            ) : knowledgeItems.length > 0 ? (
              <List>
                {knowledgeItems.map((item) => (
                  <React.Fragment key={item.id}>
                    <ListItem>
                      <ListItemText
                        primary={item.title}
                        secondary={`Type: ${item.type} | Added: ${new Date(item.created_at).toLocaleString()}`}
                      />
                      <ListItemSecondaryAction>
                        <IconButton edge="end" aria-label="delete">
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Typography variant="body1" color="textSecondary" sx={{ mt: 2 }}>
                No knowledge items found.
              </Typography>
            )}
            
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        )}

        {/* Escalations Tab */}
        {tabValue === 2 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Escalated Queries
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                <CircularProgress />
              </Box>
            ) : escalations.length > 0 ? (
              <List>
                {escalations.map((escalation) => (
                  <Paper key={escalation.id} elevation={2} sx={{ mb: 2, p: 2 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      User Query:
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 1 }}>
                      {escalation.query}
                    </Typography>
                    
                    <Typography variant="subtitle2" color="textSecondary">
                      Reason for Escalation:
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {escalation.reason}
                    </Typography>
                    
                    <Typography variant="caption" color="textSecondary">
                      User ID: {escalation.user_id} | Session ID: {escalation.session_id}
                    </Typography>
                    
                    <Box sx={{ mt: 2 }}>
                      <TextField
                        fullWidth
                        label="Resolution"
                        multiline
                        rows={3}
                        variant="outlined"
                        sx={{ mb: 1 }}
                      />
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<CheckCircleIcon />}
                        onClick={() => handleResolveEscalation(
                          escalation.id,
                          "This is a manual resolution",
                          escalation.user_id,
                          escalation.session_id
                        )}
                      >
                        Resolve
                      </Button>
                    </Box>
                  </Paper>
                ))}
              </List>
            ) : (
              <Typography variant="body1" color="textSecondary" sx={{ mt: 2 }}>
                No escalated queries found.
              </Typography>
            )}
            
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default AdminPage; 