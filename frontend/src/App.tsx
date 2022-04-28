import React from 'react';
import './App.css';
import { initializeIcons } from '@fluentui/react/lib/Icons';
import { LatLng, LatLngBoundsExpression } from 'leaflet';

import ETATrips from './Components/ETATrips/ETATrips';
import DKMap, { PostSetting } from './Components/Map/Map';
// import PostButton, { PostSetting } from './Components/PostButton';
import Filters, { FilterObj } from './Components/Filters/Filters';
import GridSetting, { GridSettingObj } from './Components/GridSetting/GridSetting';

export interface Trip {
	tripId: number;
	// lineString: LatLng[]
	eta: string;
	color: string;
	shipType: string;
	mmsi?: number;
	imo?: number;
	typeOfMobile?: string;
	name?: string;
	width?: number;
	length?: number;
}


interface AppStates {
	pointCoords: LatLng[];
	filterShipTypes: string[];
	mouseCoords: string[];
	trips: Trip[];
	postSetting: PostSetting;
	getTrips: boolean;
	selectedTripId: number | null;
}

initializeIcons(undefined, {disableWarnings: true});

export class App extends React.Component<any, AppStates> {

	protected mapCenter: LatLng;
	protected mapBoundaries: LatLngBoundsExpression;
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
		
		this.state = {
			pointCoords: [],
			mouseCoords: [],
			trips: [],
			filterShipTypes: [],
			postSetting: { gridSetting: {size: 500, isHexagon: true}, activeFilters: null },
			selectedTripId: null,
			getTrips: false,
		}
	}

	render() {
		return (
			<div className='main'>
				<div className="main-container">
					<DKMap
						gridSettings={this.state.postSetting.gridSetting!}
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
						retSelectedTripId={(tripId: number) => {
							this.setState({selectedTripId: tripId});
						}}
						postSetting={this.state.postSetting}
						fetchTrips={this.state.getTrips}
						doneFetching={(trips: Trip[]) => {
							this.setState({getTrips: false, trips: trips});
						}}
						selectedTripId={this.state.selectedTripId}
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
								<button 
									className="button btn-find-route" 
									disabled={this.state.pointCoords.length < 2 || this.props.postSetting === null}
									onClick={() => this.setState({getTrips: true})}// this.postCoordinates(this.props.coordinates)}
								>
									Find route
								</button>
								<button
									className={'button btn-clear'}
									disabled={this.state.pointCoords.length <= 0}
									onClick={() => this.clearPoints()}
								>
									Clear point(s)
								</button>
							</div>
						</div>
						<hr />
						<ETATrips
							ref={this.ETATripsRef}
							trips={this.state.trips}
							tripsShown={16}
							selectedTripId={this.state.selectedTripId}
							returnTripIndex={(fromIndex: number, amount: number) => {
								/*Fetch the next trips from the database
								  Fetch from fromIndex and then fetch 'amount' trips*/
							}}
							retSelectedTripId={(tripId: number) => {
								this.setState({selectedTripId: tripId});
							}}
						/>
						<hr />
						<GridSetting 
							onChange={(setting: GridSettingObj) => {
								this.clearPoints();
								this.setState({
									postSetting: { 
										gridSetting: setting, 
										activeFilters: this.state.postSetting ? this.state.postSetting.activeFilters : null 
									}
								});
							}}
						/>
						<hr />
						<Filters 
							returnFilters={(filters: FilterObj) => {
								this.setState({
									postSetting: { 
										gridSetting: this.state.postSetting ? this.state.postSetting.gridSetting : null, 
										activeFilters: filters
									}
								});
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
			trips: [],
			selectedTripId: null
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
