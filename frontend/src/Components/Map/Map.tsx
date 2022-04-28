import React from 'react';
import './Map.css';
import '../../Leaflet.css'; 
import { MapConsumer, MapContainer, TileLayer } from 'react-leaflet';    
import L, { LatLngBoundsExpression, LatLng, FeatureGroup } from 'leaflet';
import iconUrl from '../../Images/GreenCircle.png';
import MapEvents from './MapEvents';
import countries from './countries';
import { Feature, FeatureCollection, GeoJsonObject } from 'geojson';
import { GridSettingObj } from '../GridSetting/GridSetting'
import { Trip } from '../../App';
import { FilterObj } from '../Filters/Filters';

export interface PostSetting {
	gridSetting: GridSettingObj | null;
	activeFilters: FilterObj | null;
}

interface DKMapProps {
    mapBounds: LatLngBoundsExpression;
    mapCenter: LatLng;
    gridSettings: GridSettingObj;
    retCoords: (coords: LatLng[]) => void;
    retMousePos: (pos: string[]) => void;
    
    selectedTripId: number | null;
    retSelectedTripId: (tripId: number) => void;

    postSetting: PostSetting | null;
    fetchTrips: boolean;
    doneFetching: (trips: Trip[]) => void;
}

interface DKMapStates {
    points: LatLng[];
    hexPolygons: L.Polygon[];
    fetching: boolean;
    mapRef: L.Map | null;
}

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected markerLayer: L.LayerGroup;
    protected lineStringLayer: L.LayerGroup;
    protected linestrings: L.Polyline[];
    protected markerIcon: L.DivIcon;
    protected countriesAdded: boolean;
    protected ignoreCountries: L.Layer[];
    protected hexagons: L.Polygon[];
    protected fetching: boolean;

    // protected mapRef: React.RefObject<L.Map>;

    constructor(props: DKMapProps) {
        super(props);
        this.fetching = false;
        this.ignoreCountries = [];
        this.countriesAdded = false;
        this.hexagons = [];
        this.linestrings = [];
        this.markerLayer = L.layerGroup();
        this.lineStringLayer = L.layerGroup();
        this.markerIcon = L.icon({
            className: 'marker',
            iconUrl: iconUrl,
            iconSize: [20,20],
            iconAnchor: [10,10]
        });

        this.state = {
            points: [],
            hexPolygons: [],
            fetching: false,
            mapRef: null,
            // linestrings: [],
        }

        // this.mapRef = React.createRef();
    }

    componentDidUpdate() {
        if(this.state.mapRef && this.props.fetchTrips) {
            this.fetchTrips();
        }
        // if (this.props.selectedTripId) {
        //     this.lineStringLayer.eachLayer((layer: L.Layer) => {
        //         // this.lineStringLayer.hasLayer()
        //     });
        // }
    }
    
    render() {
        if(this.state.mapRef) {
            this.lineStringLayer.addTo(this.state.mapRef);
        }
        return (
            <MapContainer
                whenCreated={(map) => { this.setState({mapRef: map}) }}
                id='map'
                className="map-container"
                center={this.props.mapCenter}
                // bounds={MAP_BOUNDS}
                zoom={7}
                minZoom={1}
                maxZoom={50}
                scrollWheelZoom={true}
                maxBounds={this.props.mapBounds}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    // bounds={MAP_BOUNDS}
                />
                <MapConsumer>
                    {(map) => {
                        if(!this.countriesAdded) { 
                            this.addCountryPolygons(map);                        
                        }
                        this.state.hexPolygons.map((poly) => {
                            return poly.addTo(map); 
                        });
                        return null;
                    }}
                </MapConsumer>
                <MapEvents 
                    ignoreLayers={this.ignoreCountries}
                    layerGroup={this.markerLayer}
                    markerIcon={this.markerIcon}
                    points={this.state.points}
                    fetchHexagon={(point) => this.fetchPolygon(point)}
                    retMouseCoords={(pos: string[]) => this.props.retMousePos(pos)}
                    addPoint={(point) => {
                        this.state.points.push(point);
                        this.fetchPolygon(point);
                        this.props.retCoords(this.state.points);
                        this.setState({points: this.state.points});
                        }}
                    clearPoints={() => this.clear}
                ></MapEvents>
            </MapContainer>
        );
    }

    public clear() {
        this.state.hexPolygons.forEach((hex)=>{
            hex.remove();
        });
        this.linestrings.forEach((linestring) => {
            linestring.remove();
        });
        this.lineStringLayer.clearLayers();
        this.markerLayer.clearLayers();
        this.linestrings = [];
        this.setState({points: [], hexPolygons: []});
    }

    protected async fetchPolygon(point: LatLng) {
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
                        "long": point.lng,
                        "lat": point.lat,
                        "is_hexagon": this.props.gridSettings.isHexagon,
                        "grid_size": this.props.gridSettings.size
                    }
                )
        };
        fetch('http://' + process.env.REACT_APP_API! + '/grids/polygon', requestOptions)
        .then((response) => {
            if(!response.ok){
                return null;
            } 
            else return response.json();
        })
        .then((data: L.LatLngExpression[][] | null) => {
            if (data){
                let temp: L.Polygon[] = this.state.hexPolygons;         
                temp.push(new L.Polygon(data, {
                    opacity: 0,
                    fillOpacity: 0.6,
                }));
                if(temp.length === 1) {
                    temp[0].bindPopup("Choose a point further from your first point!");
                }
                this.setState({hexPolygons: temp});
            }
        });
    }

    protected addCountryPolygons(map: L.Map) {
        let layer = L.geoJSON(countries as GeoJsonObject, 
            {
                onEachFeature: this.onEachFeature, 
                style: {
                    opacity: 0,
                    fillOpacity: 0,
                    fillColor: "#90959e"
                }
            }).addTo(map);
        if(this.state.hexPolygons.length === 1) {
            layer.addData(this.state.hexPolygons[0] as unknown as GeoJsonObject)
        }
        this.countriesAdded = true;
    }

    protected onEachFeature(feature: any, layer: L.Layer) {
        if(this.ignoreCountries !== undefined) {
            this.ignoreCountries.push(layer);
        }
        else {
            this.ignoreCountries = [];
            this.ignoreCountries.push(layer);
        }
        layer.bindPopup("You have pressed: " + feature.properties.ADMIN + "<br>Press the water to place a point!");
    }

    protected async fetchTrips(){
        if(this.state.points.length !== 2) {
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
                        "long": this.state.points[0].lng,
                        "lat": this.state.points[0].lat,
                        "is_hexagon": this.props.postSetting?.gridSetting?.isHexagon,
                        "grid_size": this.props.postSetting?.gridSetting?.size
                },
                    "p2":{
                        "long": this.state.points[1].lng,
                        "lat": this.state.points[1].lat,
                        "is_hexagon": this.props.postSetting?.gridSetting?.isHexagon,
                        "grid_size": this.props.postSetting?.gridSetting?.size
                }
            })
        };
        let trips: Trip[] = [];
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
                    console.log(feature.properties.simplified_trip_id);
                    featureLayer.bindPopup("ID: " + feature.properties.simplified_trip_id);
                    featureLayer.addEventListener("click", () => this.props.retSelectedTripId(feature.properties.simplified_trip_id));
                    this.lineStringLayer.addLayer(featureLayer);        
                },
                style: (feature) => {
                    return {
                        color: feature?.properties.color,
                        opacity: (!this.props.selectedTripId || this.props.selectedTripId === feature?.properties.simplified_trip_id) ? 1 : 0,
                        //     if(!this.props.selectedTripId) {
                        //         return 1;
                        //     }
                        //     if(feature?.properties.simplified_trip_id === this.props.selectedTripId) {
                        //         return 1;
                        //     }
                        //     return 0;
                        // ,
                        weight: 4,
                    }
                }
            });
        }
        this.props.doneFetching(trips);
      };
}

export default DKMap;