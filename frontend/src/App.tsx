import React from 'react';
import './App.css';
import LeafletMap from './Components/LeafletMap';
import DKMap from './Components/Map';
import './Leaflet.css';

function App() {
  return (
    <div className="main-container">
        <LeafletMap />
    </div>
  );
}

export default App;
