import React from 'react';
import './Map.css';
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet';    
import '../Leaflet.css';
import L, { LatLngBoundsExpression, LatLngExpression, LatLng, LeafletMouseEvent, icon } from 'leaflet';
import iconUrl from '../Images/GreenCircle.png';

interface DKMapProps {
    retCoords: (coords: LatLng[]) => void;
    mapBounds: LatLngBoundsExpression;
    mapCenter: LatLng;
}

interface DKMapStates {
    points: LatLng[];
}

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected gridJSON: any;
    protected markerLayer: L.LayerGroup;
    protected markerIcon: L.DivIcon;

    constructor(props: DKMapProps) {
        super(props);
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
                    // bounds={this.props.mapBounds}
                />
                <ClickMap 
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
}

export default DKMap;


interface ClickMapProps {
    points: LatLng[];
    layerGroup: L.LayerGroup;
    addPoint: (pos: LatLng) => void;
    clearPoints: () => void;
    markerIcon: L.DivIcon;
}


function ClickMap(props: ClickMapProps) {
    const map = useMapEvents({
        click: (event) => {
            if (props.points.length < 2) {
                addMarker(event);
            }
            else {
                clearMarkers();
            }
        }
    });

    if(!map.hasLayer(props.layerGroup)) {
        map.addLayer(props.layerGroup);
    }

    function addMarker(e: LeafletMouseEvent) {
        let position: LatLng = new LatLng(e.latlng.lat, e.latlng.lng);
        props.layerGroup.addLayer(L.marker(position, {icon: props.markerIcon}).bindPopup("Lat: " + position.lat + " Lng: " + position.lng));
        props.addPoint(position);
    }

    function clearMarkers() {
        props.layerGroup.clearLayers();
        props.clearPoints();
    }
    return null;
}