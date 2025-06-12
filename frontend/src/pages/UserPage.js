import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  IconButton,
  AppBar,
  Toolbar,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import HistoryIcon from '@mui/icons-material/History';
import ChatInterface from '../components/ChatInterface';
import { userApi } from '../services/api';

const UserPage = () => {
  const [userId, setUserId] = useState('user-123'); // In a real app, this would come from auth
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const drawerWidth = 240;

  useEffect(() => {
    // Load user sessions
    const loadSessions = async () => {
      try {
        const response = await userApi.getSessions(userId);
        if (response.data && response.data.sessions) {
          setSessions(response.data.sessions);
          
          // If no active session, use the most recent one
          if (!sessionId && response.data.sessions.length > 0) {
            setSessionId(response.data.sessions[0].id);
          }
        }
      } catch (error) {
        console.error('Error loading sessions:', error);
      }
    };
    
    if (userId) {
      loadSessions();
    }
  }, [userId]);

  const handleSessionSelect = (id) => {
    setSessionId(id);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  const handleNewSession = () => {
    setSessionId(null);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const drawer = (
    <>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Sessions
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={handleNewSession}>
            <ListItemText primary="New Conversation" />
          </ListItemButton>
        </ListItem>
      </List>
      <Divider />
      <List>
        {sessions.map((session) => (
          <ListItem key={session.id} disablePadding>
            <ListItemButton
              selected={sessionId === session.id}
              onClick={() => handleSessionSelect(session.id)}
            >
              <ListItemText
                primary={session.title || `Session ${session.id.slice(0, 8)}`}
                secondary={formatDate(session.last_updated)}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setDrawerOpen(!drawerOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            FinMate AI Assistant
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Drawer for session history */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8, // Account for AppBar height
          height: 'calc(100vh - 64px)', // Full height minus AppBar
        }}
      >
        <Paper
          elevation={3}
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            p: 2,
          }}
        >
          <ChatInterface
            userId={userId}
            sessionId={sessionId}
            setSessionId={setSessionId}
          />
        </Paper>
      </Box>
    </Box>
  );
};

export default UserPage; 