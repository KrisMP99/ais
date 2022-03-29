import { LatLng, LatLngBoundsExpression } from 'leaflet';
import React from 'react';
import './App.css';
import DKMap from './Components/Map/Map';
import PostButton from './Components/PostButton';
import './Leaflet.css';

interface AppStates {
  pointCoords: LatLng[];
  mouseCoords: string[];
  polylines: LatLng[];
}

export class App extends React.Component<any, AppStates> {

  protected mapCenter: LatLng;
  protected mapBoundaries: LatLngBoundsExpression;

  constructor(props: any) {
    super(props);
    this.mapCenter = new LatLng(55.8581, 9.8476);
    this.mapBoundaries = [[58.5, 3.2], [53.5, 16.5]];
    this.state = {
      pointCoords: [],
      mouseCoords: [],
      polylines: []
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
              this.setState({ pointCoords: points });
            }}
            retMousePos={(pos: string[]) => { this.setState({ mouseCoords: pos }); }}
            polylines={this.state.polylines}
          />
          <div className='right-side'>
            <div className='positions-container'>
              <p className='text-1'>Positions:</p>
              <div>
                <p className='text-2'>
                  Current mouse location:<br />
                  Lat: {this.textIsNotUndefined(0, true)} Lng: {this.textIsNotUndefined(0, false)}
                </p>
                <p className='text-2'>
                  Point 1:<br />
                  Lat: {this.textIsNotUndefined(1, true)} Lng: {this.textIsNotUndefined(1, false)}
                </p>
                <p className='text-2'>
                  Point 2:<br />
                  Lat: {this.textIsNotUndefined(2, true)} Lng: {this.textIsNotUndefined(2, false)}
                </p>
              </div>
              <PostButton
                coordinates={this.state.pointCoords}
                getData={(data: LatLng[]) => this.setState({ polylines: data })}
              />
            </div>
            <div className='filter-container'>
            </div>
          </div>
        </div>
      </div>
    );
  }

  protected textIsNotUndefined(index: number, lat: boolean): string {
    if (this.state.mouseCoords && index == 0) {
      return lat ? this.state.mouseCoords[0] : this.state.mouseCoords[1];
    }
    if (this.state.pointCoords.length >= 1 && index == 1) {
      return lat ? this.state.pointCoords[0].lat.toFixed(4) : this.state.pointCoords[0].lng.toFixed(4);
    }
    else if (this.state.pointCoords.length == 2 && index == 2) {
      return lat ? this.state.pointCoords[1].lat.toFixed(4) : this.state.pointCoords[1].lng.toFixed(4);
    }
    return "0";
  }
}

export default App;
