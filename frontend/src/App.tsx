import React from 'react';
import './App.css';
import DKMap from './Components/Map';
import PostButton from './Components/PostButton';
import './Leaflet.css';

function App() {
  return (
    <div className='main'>
      <div className="main-container">
          <DKMap />
          <PostButton/>
      </div>
    </div>
  );
}

export default App;
