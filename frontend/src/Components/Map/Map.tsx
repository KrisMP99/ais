import React from 'react';
import './Map.css';
import '../../Leaflet.css';
import { MapConsumer, MapContainer, TileLayer, useMap } from 'react-leaflet';    
import L, { LatLngBoundsExpression, LatLng } from 'leaflet';
import iconUrl from '../../Images/GreenCircle.png';
import MapEvents from './MapEvents';
import countries from './countries';
import { GeoJsonObject } from 'geojson';

interface DKMapProps {
    mapBounds: LatLngBoundsExpression;
    mapCenter: LatLng;

    retCoords: (coords: LatLng[]) => void;
    retMousePos: (pos: string[]) => void;
}

interface DKMapStates {
    points: LatLng[];
}

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
                center={this.props.mapCenter}
                bounds={this.props.mapBounds}
                zoom={7}
                minZoom={7}
                maxZoom={12}
                scrollWheelZoom={true}
                maxBounds={this.props.mapBounds}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapConsumer>
                    {(map) => {
                        if(!this.countriesAdded) { 
                            this.addCountryPolygons(map);                        
                        }
                        return null;
                    }}
                </MapConsumer>
                <MapEvents 
                    ignoreLayers={this.ignoreCountires}
                    layerGroup={this.markerLayer}
                    markerIcon={this.markerIcon}
                    points={this.state.points}
                    retMouseCoords={(pos: string[]) => this.props.retMousePos(pos)}
                    addPoint={(point) => {
                            if(this.state.points) {
                                this.state.points.push(point);
                                this.props.retCoords(this.state.points);
                                this.setState({points: this.state.points});
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