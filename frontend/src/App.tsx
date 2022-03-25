import { LatLng, LatLngBoundsExpression } from 'leaflet';
import React from 'react';
import './App.css';
import DKMap from './Components/Map/Map';
import PostButton from './Components/PostButton';
import './Leaflet.css';

interface AppStates {
  pointCoords: LatLng[];
}

export class App extends React.Component<any, AppStates> {

  protected mapCenter: LatLng;
  protected mapBoundaries: LatLngBoundsExpression;

  constructor(props: any) {
    super(props);
    this.mapCenter = new LatLng(55.8581, 9.8476);
    this.mapBoundaries = [[58.5, 3.2], [53.5, 16.5]];
    this.state = {
      pointCoords: []
    }
  }

  render() {

    return (
      <div className='main'>
        <div className="main-container">
          <DKMap
            mapCenter={this.mapCenter}
            mapBounds={this.mapBoundaries}
            retCoords={(points: LatLng[]) => {
              this.setState({pointCoords: points});
            }}
          />
          <PostButton 
            coords={this.state.pointCoords}
          />
        </div>
      </div>
    );
  }
}

export default App;
