import { LatLng } from 'leaflet';
import React, { useState } from 'react';
import './App.css';
import DKMap from './Components/Map/Map';
import PostButton from './Components/PostButton';
import './Leaflet.css';

interface AppProps {

}
interface AppStates {
  pointCoords: LatLng[];
}


export class App extends React.Component<AppProps, AppStates> {
  // const [pointCoords, setPointCoords] = useState([])
  // var pointCoords: LatLngExpression[];
  constructor(props: AppProps) {
    super(props);

    this.state = {
      pointCoords: []
    }
  }

  render() {

    return (
      <div className='main'>
        <div className="main-container">
          <DKMap
            retCoords={(points: LatLng[]) => {
              this.setState({pointCoords: points});
            }}
          />
          <PostButton 
            coordinates={this.state.pointCoords}
          />
        </div>
      </div>
    );
  }
}

export default App;
