import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './Home'
import Prompt from './Prompt'
function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/prompt" element={<Prompt />} />
    </Routes>
  )
}

export default App;