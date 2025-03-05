import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './Home';
import Prompt from './Prompt';
import IDE from './IDE';
import axios from 'axios';

// Configure axios to connect to Flask backend
axios.defaults.baseURL = 'http://localhost:5015'; // Ensure Flask backend is running on this port

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/prompt" element={<Prompt />} />
      <Route path="/ide" element={<IDE />} />
    </Routes>
  );
}

export default App;
