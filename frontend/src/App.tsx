import { LatLng, LatLngBoundsExpression } from 'leaflet';
import React from 'react';
import './App.css';
import ETATrips from './Components/ETATrips/ETATrips';
import DKMap from './Components/Map/Map';
import PostButton from './Components/PostButton';
import ShipTypeFilter from './Components/Filters/ShipTypeFilter/ShipTypeFilter';

export interface Trip {
	tripId: number;
	tripPolyline?: LatLng[][]
	color: string;
	totalTime: string;
	shipType?: string;
}

interface AppStates {
	pointCoords: LatLng[];
	filterShipTypes: string[];
	mouseCoords: string[];
	polylines: LatLng[][];
	trips: Trip[];
}

export class App extends React.Component<any, AppStates> {

	protected mapCenter: LatLng;
	protected mapBoundaries: LatLngBoundsExpression;
	protected temporaryTrips: Trip[];
	protected ETATripsRef: React.RefObject<ETATrips>;
	protected DKMapRef: React.RefObject<DKMap>;
	protected mousePosRef: React.RefObject<HTMLParagraphElement>;

	constructor(props: any) {
		super(props);
		
		this.ETATripsRef = React.createRef();
		this.DKMapRef = React.createRef();
		this.mousePosRef = React.createRef();

		this.mapCenter = new LatLng(55.8581, 9.8476);
		this.mapBoundaries = [[58.5, 3.2], [53.5, 16.5]];
		this.temporaryTrips = [];
		for (let i = 0; i < 130; i++) {
			this.temporaryTrips.push({ color: 'red', totalTime: '30min', tripId: i });   //DUMMY DATA
		}
		this.state = {
			pointCoords: [],
			mouseCoords: [],
			trips: [],
			polylines: [],
			filterShipTypes: [],
		}
	}

	render() {
		return (
			<div className='main'>
				<div className="main-container">
					<DKMap
						ref={this.DKMapRef}
						mapCenter={this.mapCenter}
						mapBounds={this.mapBoundaries}
						retCoords={(points: LatLng[]) => {
							this.setState({ pointCoords: points });
						}}
						retMousePos={(pos: string[]) => { 
							if(this.mousePosRef.current) {
								this.mousePosRef.current.innerText = 
								"Current mouse location:\nLat: " + this.textIsNotUndefined(0, true, pos) + " Lng: " + this.textIsNotUndefined(0, false, pos); 
							}
						}}
						polylines={this.state.polylines}
					/>
					<div className='right-side'>
						<div className='positions-container'>
							<p className='text-1'>Positions:</p>
							<div>
								<p ref={this.mousePosRef} className='text-2'>
									Current mouse location:<br />
									Lat: 0.0000 Lng: 0.0000
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
							<div className='footer'>
								<PostButton
									coordinates={this.state.pointCoords}
									shipTypeArray={this.state.filterShipTypes}
									getData={(data: LatLng[][]) => this.setState({ polylines: data })}
								/>
								<button
									className={'button btn-clear'}
									disabled={this.state.pointCoords.length <= 0}
									onClick={() => this.clearPoints()}
								>
									Clear
								</button>
							</div>
						</div>
						<hr />
						<ETATrips
							ref={this.ETATripsRef}
							trips={this.state.trips} //DENNE HER ER DUMMY DATA - SKAL GØRES TIL DE FAKTISKE TRIPS
							tripsShown={16}
						/>
						<hr />
						<ShipTypeFilter
							returnShipType={(shipTypes: string[]) => {
								this.setState({filterShipTypes: shipTypes});
							}}
						/>
					</div>
				</div>

			</div>
		);
	}

	protected clearPoints() {
		this.DKMapRef.current?.clear();
		this.setState({
			pointCoords: [],
			mouseCoords: [],
			polylines: [],
		});
	}

	protected textIsNotUndefined(index: number, lat: boolean, pos?: string[]): string {
		if (this.state.mouseCoords && index === 0 && pos) {
			return lat ? pos[0] : pos[1];
		}
		if (this.state.pointCoords.length >= 1 && index === 1) {
			return lat ? this.state.pointCoords[0].lat.toFixed(4) : this.state.pointCoords[0].lng.toFixed(4);
		}
		else if (this.state.pointCoords.length === 2 && index === 2) {
			return lat ? this.state.pointCoords[1].lat.toFixed(4) : this.state.pointCoords[1].lng.toFixed(4);
		}
		return "0.0000";
	}
}

export default App;
