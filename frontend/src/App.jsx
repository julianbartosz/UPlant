import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Garden from './components/GardenSection/Garden'

function App() {
  
  // TODO: 
  // This is a temporary solution, we will need to fetch the garden and cells from the backend
const garden = { x: 5, y: 5 }

const cells = [
  ["🍅", "🥕", "🌽", "🍆", "🥦"],
  ["🌳", "🌲", null, null, null],
  Array(garden.x).fill(null),
  Array(garden.x).fill(null),
  Array(garden.x).fill(null)
]

  return (
    <div style={{ width: '90vw', height: '90vh', alignItems: 'center', display: 'flex', justifyContent: 'center' }}> 
      <Garden cells={cells} garden={garden} />
    </div>
  )
}

export default App
