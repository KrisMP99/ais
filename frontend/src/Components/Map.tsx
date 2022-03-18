import React, { useState } from 'react';
import './Map.css';
import Hexagon from './Hexagon'
import { MapContainer, TileLayer, Marker, Polygon, Polyline, MapConsumer, useMapEvents, useMap } from 'react-leaflet';    
import '../Leaflet.css';
import L, { LatLngBoundsExpression, LatLngExpression, LatLng, Icon, LeafletMouseEvent, marker } from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import * as testsss from "../test.json";
import Helmet from 'react-helmet';
import { GeoJSON, GeoJsonObject} from 'geojson'
import { useMapElement } from 'react-leaflet/types/MapContainer';
import { AnyMxRecord } from 'dns';

interface DKMapProps {

}

interface DKMapStates {
    points: LatLngExpression[];
}

const MAP_CENTER: LatLng = new LatLng(55.8581, 9.8476);
const MAP_BOUNDS: LatLngBoundsExpression = [[58.5, 3.2], [53.5, 16.5]];

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected gridJSON: any;
    protected markerLayer: L.LayerGroup;

    constructor(props: DKMapProps) {
        super(props);
        this.markerLayer = L.layerGroup();
        this.state = {
            points: []
        }
    }

    protected async retrieveGridJson() {
        this.gridJSON = await fetch('http://127.0.0.1:8008/map_bounds?access_token=' + process.env.REACT_APP_API_KEY).then(res => res.json());
    }

    componentDidMount() {
        this.retrieveGridJson();
    }

    render() {
        // Sets the icon of the markers
        let DefaultIcon = L.icon({
            iconUrl: icon,
            shadowUrl: iconShadow
        });
        L.Marker.prototype.options.icon = DefaultIcon;

        
        
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
                <ClickMap 
                    layerGroup={this.markerLayer}
                    points={this.state.points}
                    addPoint={(point) => {
                            if(this.state.points) {
                                this.state.points.push(point);
                                this.setState({points: this.state.points});
                            }
                            else {
                                let temp: LatLngExpression[] = [];
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
    points: LatLngExpression[];
    layerGroup: L.LayerGroup;
    addPoint: (pos: LatLngExpression) => void;
    clearPoints: () => void;

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
        let position: LatLngExpression = [e.latlng.lat, e.latlng.lng];
        props.layerGroup.addLayer(L.marker(position));
        props.addPoint(position);
    }

    function clearMarkers() {
        props.layerGroup.clearLayers();
        console.log("Cleared your points!");
        props.clearPoints();
    }
    return null;
}