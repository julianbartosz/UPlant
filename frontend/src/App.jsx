
import './App.css'
import Garden from './components/GardenSection/Garden'
import NavBar from './components/NavBarSection/NavBar';
import SearchPlants from './components/SearchSection/SearchPlants'

function App() {

  // Placeholder
  const cells = [
    ["🍅", "🥕", "🌽", "🍆", "🥦"],
    ["🌳", "🌲", null, null, null],
    Array(5).fill(null),
    Array(5).fill(null),
    Array(5).fill(null),
  ];

  // TODO: Retrieve username
  const username = "Johnny Appleseed";

  // TODO: Retrieve Gardens
  const gardens = [{name: 'Garden 1', x: 5, y: 5, cells: cells}, {name: 'Garden 2', x: 5, y: 5, cells: cells}, {name: 'Garden 3', x:5, y: 5, cells: cells}]; 

  // TODO: Retrieve Plants matching search
  const plantslist = [
    { name: "🌽", description: "Description 1" },
    { name: "🥦", description: "Description 2" },
    { name: "🥕", description: "Description 3" },
    { name: "🌳", description: "Description 4" },
  ];

  return (
     <div className= 'app' style={{backgroundColor: 'white', width: '100vw', height: '100vh',position: 'relative' }}>
     <NavBar username={username}/> 
      <div className="sidebar" style={{
        position: 'fixed', top: '60px', left: 0, width: '200px', height: 'calc(100vh - 60px)',
        background: 'grey', padding: '10px', zIndex: 5
      }}> 
      <SearchPlants plants={plantslist} />
      </div>
      <div className="content" style={{
        position: 'fixed', top: '60px', left: '240px', width: 'calc(100vw - 200px)',
        height: 'calc(100vh - 60px)', background: '#eee',
        display: 'flex', justifyContent: 'center', alignItems: 'center'
      }}>
        <Garden gardens={gardens} />
      </div>
    </div>  

)
}

export default App;
