import React from 'react';
import './Map.css';
import '../../Leaflet.css'; 
import { MapConsumer, MapContainer, TileLayer, Polyline} from 'react-leaflet';    
import L, { LatLngBoundsExpression, LatLng, marker } from 'leaflet';
import iconUrl from '../../Images/GreenCircle.png';
import MapEvents from './MapEvents';
import countries from './countries';
import { GeoJsonObject } from 'geojson';
import { GridSettingObj } from '../GridSetting/GridSetting'

interface DKMapProps {
    mapBounds: LatLngBoundsExpression;
    mapCenter: LatLng;
    gridSettings: GridSettingObj;
    retCoords: (coords: LatLng[]) => void;
    retMousePos: (pos: string[]) => void;
    polylines: LatLng[][];
}

interface DKMapStates {
    points: LatLng[];
    hexPolygons: L.Polygon[];
}

function getPolylineColor(){
    return 'RGB('+ Math.random()*255 + ',' + Math.random()*255 + ',' + Math.random()*255 + ')';
}

function createPolyline(polyline: LatLng[], key: number){
    return <Polyline positions={polyline} key={key} color={getPolylineColor()} weight={5}/>
}

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected markerLayer: L.LayerGroup;
    protected markerIcon: L.DivIcon;
    protected countriesAdded: boolean;
    protected ignoreCountries: L.Layer[];
    protected hexagons: L.Polygon[];

    constructor(props: DKMapProps) {
        super(props);

        this.ignoreCountries = [];
        this.countriesAdded = false;
        this.hexagons = [];

        this.markerLayer = L.layerGroup();
        this.markerIcon = L.icon({
            className: 'marker',
            iconUrl: iconUrl,
            iconSize: [20,20],
            iconAnchor: [10,10]
        });

        this.state = {
            points: [],
            hexPolygons: [],
        }
    }

    render() {
        return (
            <MapContainer
                id='map'
                className="map-container"
                center={this.props.mapCenter}
                // bounds={MAP_BOUNDS}
                zoom={7}
                minZoom={5}
                maxZoom={14}
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
                        })
                        return null;
                    }}
                </MapConsumer>
                {this.props.polylines.map((polyline, key) => createPolyline(polyline, key))}
                <Polyline
                    positions={this.props.polylines}
                />
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
                <MapConsumer>
                    {(map) => {
                        if(!this.countriesAdded) { 
                            this.addCountryPolygons(map);                        
                        }
                        return null;
                    }}
                </MapConsumer>
            </MapContainer>
        );
    }

    public clear() {
        this.state.hexPolygons.forEach((hex)=>{
            hex.remove();
        });
        this.markerLayer.clearLayers();
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
            console.log(data)
            if (data){
                let temp: L.Polygon[] = this.state.hexPolygons;         
                temp.push(new L.Polygon(data, {
                    opacity: 0,
                    fillOpacity: 1,
                    fillColor: "#000000"
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
}

export default DKMap;