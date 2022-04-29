import React from 'react';
import './App.css';
import { Label, Spinner, SpinnerSize, IStackProps, Stack } from '@fluentui/react'
import L, { LatLng, LatLngBoundsExpression } from 'leaflet';
//COMPONENTS
import ETATrips from './Components/ETATrips/ETATrips';
import DKMap from './Components/Map/Map';
import Filters, { FilterObj } from './Components/Filters/Filters';
import GridSetting, { GridSettingObj } from './Components/GridSetting/GridSetting';

export interface PostSetting {
	gridSetting: GridSettingObj | null;
	activeFilters: FilterObj | null;
}

export interface Trip {
	tripId: number;
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
	mouseCoords: string[];
	trips: Trip[];
	postSetting: PostSetting;
	selectedTripId: number | null;
	isFetching: boolean;
	lineStringLayer: L.LayerGroup;
}

export class App extends React.Component<any, AppStates> {

	protected mapCenter: LatLng;
	protected mapBoundaries: LatLngBoundsExpression;
	protected ETATripsRef: React.RefObject<ETATrips>;
	protected DKMapRef: React.RefObject<DKMap>;
	protected mousePosRef: React.RefObject<HTMLParagraphElement>;
	protected findRouteRef: React.RefObject<HTMLButtonElement>;

	constructor(props: any) {
		super(props);
		this.ETATripsRef = React.createRef();
		this.DKMapRef = React.createRef();
		this.mousePosRef = React.createRef();
		this.findRouteRef = React.createRef();

		this.mapCenter = new LatLng(55.8581, 9.8476);
		this.mapBoundaries = [[58.5, 3.2], [53.5, 16.5]];
		
		this.state = {
			pointCoords: [],
			mouseCoords: [],
			trips: [],
			postSetting: { gridSetting: {size: 500, isHexagon: true}, activeFilters: null },
			selectedTripId: null,
			lineStringLayer: L.layerGroup(),
			isFetching: false,
		}
	}

	render() {
		const rowProps: IStackProps = { horizontal: true, verticalAlign: 'center' };

		const tokens = {
			spinnerStack: {
			childrenGap: 8,
			},
		};

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
						trips={this.state.lineStringLayer}
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
									ref={this.findRouteRef} 
									className='button btn-find-route' 
									disabled={this.state.pointCoords.length < 2 || this.props.postSetting === null}
									onClick={() => this.setState({isFetching: true})}// this.postCoordinates(this.props.coordinates)}
								>
									<div style={{display: 'flex', justifyContent: 'center'}}>
										<Stack {...rowProps} tokens={tokens.spinnerStack} >
											<Label 
												style={{color: '#fff', fontSize: '15px', fontWeight: '500'}}
												aria-setsize={15}>	
												Find route
											</Label>
											{!this.state.isFetching ? <div></div> :
												(<Spinner 
													size={SpinnerSize.small}
													ariaLive='assertive'
													// style={{display: 'None'}}
													className='loader'
												/>)
											}
										</Stack>
									</div>
								</button>
								<button
									className={'button btn-clear'}
									disabled={this.state.pointCoords.length <= 0}
									onClick={() => this.clearPoints()}
								>
									Clear map
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

	componentDidUpdate() {
		if(this.state.isFetching) {
			this.fetchTrips();
		}
	}

	protected clearPoints() {
		this.DKMapRef.current?.clear();
		this.ETATripsRef.current?.clear();
		this.state.lineStringLayer?.clearLayers();
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

	protected async fetchTrips(){
        if(this.state.pointCoords.length !== 2) {
			this.setState({isFetching: false});
            return;
        }
        const requestOptions = {
            method: 'POST',
            headers: { 
                'Accept': 'application/json', 
                'Content-Type': 'application/json',
                'x-token':  process.env.REACT_APP_TOKEN!,
            },
            body: 
                JSON.stringify(
                {
                    "p1": {
                        "long": this.state.pointCoords[0].lng,
                        "lat": this.state.pointCoords[0].lat,
                        "is_hexagon": this.state.postSetting.gridSetting?.isHexagon,
                        "grid_size": this.state.postSetting.gridSetting?.size
                },
                    "p2":{
                        "long": this.state.pointCoords[1].lng,
                        "lat": this.state.pointCoords[1].lat,
                        "is_hexagon": this.state.postSetting?.gridSetting?.isHexagon,
                        "grid_size": this.state.postSetting?.gridSetting?.size
                },
                    "filter":{
                        "ship_types": this.state.postSetting?.activeFilters?.shipTypes
                        // "date_range": this.props.postSetting?.activeFilters?.dateRange
                    }
            })
        };
        let trips: Trip[] = [];
		let tempLayer: L.LayerGroup = L.layerGroup();
        const response = await fetch('http://' + process.env.REACT_APP_API! + '/trips', requestOptions);
        if (response.ok) {
            const data = await response.json();
            L.geoJSON(JSON.parse(data), {
                onEachFeature: (feature, featureLayer) => {               
                    trips.push({ 
                        tripId: feature.properties.simplified_trip_id,
                        eta: feature.properties.eta,
                        color: feature.properties.color,
                        shipType: feature.properties.ship_type,
                        mmsi: feature.properties.mmsi,
                        imo: feature.properties.imo,
                        typeOfMobile: feature.properties.type_of_mobile,
                        name: feature.properties.name,
                        width: feature.properties.width,
                        length: feature.properties.length
                    }); 
                    featureLayer.bindPopup("ID: " + feature.properties.simplified_trip_id);
                    featureLayer.addEventListener("click", () => this.setState({selectedTripId: feature.properties.simplified_trip_id}));
                    tempLayer.addLayer(featureLayer);        
                },
                style: (feature) => {
                    return {
                        color: feature?.properties.color,
                        weight: 5,
                    }
                }
            });
        }
		this.setState({isFetching: false, lineStringLayer: tempLayer})
	};
}

export default App;
