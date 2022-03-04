import { Map, TileLayer, Marker, Popup } from 'react-leaflet';
import React from "react";
import './App.css';
import './leaflet.css';
import Leaflet from 'leaflet';
import PersonalMarker from './Model/Marker';
import { useState } from 'react';

function App() {

  const mapCenter = [55.8581, 9.8476];
  const mapBounds = [[58.577361, 4.637123], [53.2149, 14.5386]];

  const [markers, addMarker] = useState();

  return (
    <div className='main-container'>
      <Map
        center={mapCenter}
        zoom={7}
        scrollWheelZoom={true}
        onClick={(e) => addSingleMarker(e) }
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          bounds={mapBounds} 
                  
        />
        <PersonalMarker
          markers={markers}
        />
      </Map>
    </div>
  );
}

function addSingleMarker(e) {
  addMarker(marker.push(e.latlng));
}

export default App;
