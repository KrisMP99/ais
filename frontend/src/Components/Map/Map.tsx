import React from 'react';
import './Map.css';
import '../../Leaflet.css'; 
import { MapConsumer, MapContainer, TileLayer } from 'react-leaflet';    
import L, { LatLngBoundsExpression, LatLng } from 'leaflet';
import iconUrl from '../../Images/GreenCircle.png';
import MapEvents from './MapEvents';
import countries from './countries';
import { GeoJsonObject } from 'geojson';
import { GridSettingObj } from '../GridSetting/GridSetting';

interface DKMapProps {
    mapBounds: LatLngBoundsExpression;
    mapCenter: LatLng;
    gridSettings: GridSettingObj;
    retCoords: (coords: LatLng[]) => void;
    retMousePos: (pos: string[]) => void;

    trips: L.LayerGroup;
    selectedTripId: number | null;
    retSelectedTripId: (tripId: number) => void;
}

interface DKMapStates {
    points: LatLng[];
    polygons: L.Polygon[];
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
    protected polygonFetchSuccess: boolean;

    constructor(props: DKMapProps) {
        super(props);
        this.fetching = false;
        this.polygonFetchSuccess = false;
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
            polygons: [],
            mapRef: null,
        }
    }
    
    render() {
        if(this.state.mapRef) {
            this.props.trips.addTo(this.state.mapRef);
        }
        return (
            <MapContainer
                whenCreated={(map) => {  
                    this.setState({mapRef: map}); 
                }}
                id='map'
                className="map-container"
                center={this.props.mapCenter}
                bounds={this.props.mapBounds}
                zoom={7}
                minZoom={7}
                maxZoom={18}
                scrollWheelZoom={true}
                maxBounds={this.props.mapBounds}  
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    bounds={this.props.mapBounds}
                />
                <MapConsumer>
                    {(map) => {
                        if(!this.countriesAdded) { 
                            this.addCountryPolygons(map);                        
                        }
                        this.state.polygons.map((poly) => {
                            return poly.addTo(map); 
                        });
                        return null;
                    }}
                </MapConsumer>
                <MapEvents 
                    ignoreLayers={this.ignoreCountries}
                    layerGroup={this.markerLayer}
                    // markerIcon={this.markerIcon}
                    points={this.state.points}
                    retMouseCoords={(pos: string[]) => this.props.retMousePos(pos)}
                    addPoint={async (point) => {
                        await this.fetchPolygon(point)
                        if (this.polygonFetchSuccess) {
                            this.state.points.push(point);
                            this.props.retCoords(this.state.points);
                            this.setState({points: this.state.points});
                        }}
                    }
                    clearPoints={() => this.clear}
                ></MapEvents>
            </MapContainer>
        );
    }

    public clear() {
        this.state.polygons.forEach((hex)=>{
            hex.remove();
        });
        this.linestrings.forEach((linestring) => {
            linestring.remove();
        });
        this.lineStringLayer.clearLayers();
        this.markerLayer.clearLayers();
        this.linestrings = [];
        this.props.trips.clearLayers();

        this.setState({points: [], polygons: []});
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
        try {
            await fetch('http://' + process.env.REACT_APP_API! + '/grids/polygon', requestOptions)
            .then((response) => {
                if(!response.ok){
                    this.polygonFetchSuccess = false;
                    alert("Could not find any polygon at the given point");
                    return null;
                } 
                else {
                    return response.json(); 
                }
            })
            .then((data: L.LatLngExpression[][] | null) => {
                if (data && this.state.polygons.length < 2){
                    let temp: L.Polygon[] = this.state.polygons;         
                    temp.push(new L.Polygon(data, {
                        opacity: 0,
                        fillOpacity: 0.6,
                    }));
                    if (temp.length === 1) {
                        temp[0].bindPopup("Choose a point further from your first point!");
                    }
                    else if (temp.length === 2) {
                        temp[0].unbindPopup();
                    }
                    if (this.state.polygons.length < 2 && temp.length <= 2) {
                        this.polygonFetchSuccess = true;
                        this.setState({polygons: temp});
                        return true;
                    }
                }
                else {
                    this.polygonFetchSuccess = false;
                }
            });
        }
        catch {
            alert("OOPS...\nCould not fetch grid polygon");
        }
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
        if(this.state.polygons.length === 1) {
            layer.addData(this.state.polygons[0] as unknown as GeoJsonObject)
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
}

export default DKMap;