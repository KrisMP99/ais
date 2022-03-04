import React from 'react';
import { Map, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import './Marker.css';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png'; 

export class PersonalMarker extends React.Component {
    constructor() {
      super();
      this.state = {
        markers: props.markers
      };
    }
    
  
    render() {
        let DefaultIcon = L.icon({
            iconUrl: icon,
            shadowUrl: iconShadow
        });
        L.Marker.prototype.options.icon = DefaultIcon;
        return (
            this.state.markers.map((position, idx) =>
                        <Marker key={`marker-${idx}`} position={position}></Marker>
                    )
        );
    }
  }

  export default PersonalMarker;