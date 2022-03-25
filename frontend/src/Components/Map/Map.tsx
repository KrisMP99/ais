import React from 'react';
import './Map.css';
import { MapConsumer, MapContainer, TileLayer, useMap } from 'react-leaflet';    
import '../../Leaflet.css';
import L, { LatLngBoundsExpression, LatLng } from 'leaflet';
import iconUrl from '../../Images/GreenCircle.png';
import ClickMap from './PlacePoint';
import countries from './countries';
import { GeoJsonObject } from 'geojson';

interface DKMapProps {
    retCoords: (coords: LatLng[]) => void;
}

interface DKMapStates {
    points: LatLng[];
}

const MAP_CENTER: LatLng = new LatLng(55.8581, 9.8476);
const MAP_BOUNDS: LatLngBoundsExpression = [[58.5, 3.2], [53.5, 16.5]];

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected gridJSON: any;
    protected markerLayer: L.LayerGroup;
    protected markerIcon: L.DivIcon;
    protected countriesAdded: boolean;
    protected ignoreCountires: L.Layer[];

    constructor(props: DKMapProps) {
        super(props);

        this.ignoreCountires = [];
        this.countriesAdded = false;

        this.markerLayer = L.layerGroup();
        this.markerIcon = L.icon({
            className: 'marker',
            iconUrl: iconUrl,
            iconSize: [20,20],
            iconAnchor: [12,20]
        });

        this.state = {
            points: []
        }
    }

    render() {
        return (
            <MapContainer
                id='map'
                className="map-container"
                center={MAP_CENTER}
                bounds={MAP_BOUNDS}
                zoom={7}
                minZoom={7}
                maxZoom={12}
                scrollWheelZoom={true}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    bounds={MAP_BOUNDS}
                />
                <MapConsumer>
                    {(map) => {
                        if(!this.countriesAdded) { 
                            this.addCountryPolygons(map);                        
                        }
                        return null;
                    }}
                </MapConsumer>
                <ClickMap 
                    ignoreLayers={this.ignoreCountires}
                    layerGroup={this.markerLayer}
                    markerIcon={this.markerIcon}
                    points={this.state.points}
                    addPoint={(point) => {
                            if(this.state.points) {
                                this.state.points.push(point);
                                this.props.retCoords(this.state.points);
                                this.setState({points: this.state.points});
                            }
                            else {
                                let temp: LatLng[] = [];
                                temp.push(point);
                                this.setState({points: temp})
                            }
                        }}
                    clearPoints={() => {
                        this.state.points.pop();
                        this.state.points.pop();
                        this.setState({points: this.state.points});
                    }}
                />
            </MapContainer>
        );
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
        this.countriesAdded = true;
    }

    protected onEachFeature(feature: any, layer: L.Layer) {
        if(this.ignoreCountires != undefined) {
            this.ignoreCountires.push(layer);
        }
        else {
            this.ignoreCountires = [];
            this.ignoreCountires.push(layer);
        }
        layer.bindPopup("You have pressed: " + feature.properties.ADMIN + "<br>Press the water to place a point!");
    }
}

export default DKMap;