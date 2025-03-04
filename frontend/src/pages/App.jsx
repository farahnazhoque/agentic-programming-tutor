import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './Home'
import Prompt from './Prompt'
import IDE from './IDE'
function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/prompt" element={<Prompt />} />
      <Route path="/ide" element={<IDE />} />
    </Routes>
  )
}

export default App;