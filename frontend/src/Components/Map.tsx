import React from 'react';
import './Map.css';
import Hexagon from './Hexagon'
import { MapContainer, TileLayer, Marker, Polygon, Polyline } from 'react-leaflet';    
import '../Leaflet.css';
import L, { LatLngBoundsExpression, LatLngExpression, LatLng, Icon } from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import * as testsss from "../test.json";
import Helmet from 'react-helmet';
import { GeoJSON, GeoJsonObject} from 'geojson'


interface DKMapProps {

}

interface DKMapStates {
    markers: LatLngExpression[] | null;
}

const MAP_CENTER: LatLng = new LatLng(55.8581, 9.8476);
const MAP_BOUNDS: LatLngBoundsExpression = [[58.5, 3.2], [53.5, 16.5]];

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected hexagonGrid: Hexagon[] | null | undefined;
    protected gridJSON: GeoJsonObject | undefined;
    protected map: L.Map;
    
    constructor(props: DKMapProps) {
        super(props);
        this.hexagonGrid = null;
        this.map = L.map('map').setView(MAP_CENTER, 7);
        this.state = {
            markers: null
        }
    }

    protected async retrieveGridJson() {
        this.gridJSON = await fetch('http://127.0.0.1:8008/map_bounds').then(res => res.json());
    }

    protected async load_shapefile() {
    //   let url = 'http://127.0.0.1:8008/map_bounds';
    //   let shapeobject;
    //   let response = await fetch(url).then((res) => {
    //     if (!res.ok) {
    //         throw new Error("HTTP error " + res.status)
    //     }
    //     else {
    //         shapeobject= res.json
    //     }
    // });
    // // return shapeobject;
    // return fetch('http://127.0.0.1:8008/map_bounds')
    //     .then(res => res.json());
    //     console.log(s);
    }

    componentDidMount() {
        // this.map = L.map('map').setView(MAP_CENTER, 7);
        this.retrieveGridJson();
    }

    render() {
        // let map = L.map('map').setView(MAP_CENTER, 7);
        
        
        
        // .then(response => {
        //         return response.text();
        //     })
        //     .then(data => {
        //         s = data;
        //     });
        //     console.log(tem);
        // L.geoJSON(this.gridJSON).addTo('map');
        let DefaultIcon = L.icon({
            iconUrl: icon,
            shadowUrl: iconShadow
        });
        L.Marker.prototype.options.icon = DefaultIcon;
        // L.geoJSON(this.gridJSON).addTo(this.map);
        // L.control.scale().addTo(L.map)
        // let grid = this.addGrid();
        // let test = () => {
        //     testsss.features.map(park => (
        //         <Marker
        //           key={park.properties.PARK_ID}
        //           position={[
        //             park.geometry.coordinates[1],
        //             park.geometry.coordinates[0]
        //           ]}
        //         />
        //       ))
        // }

        

        return (
            <MapContainer
                id='map'
                ref={this.map}
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
                {/* <Hexagon center={MAP_CENTER} rad={600} /> */}
                {/* {() => {
                    if (this.state.markers) {
                        this.state.markers.map((pos, idx) =>
                            <Marker key={`marker-${idx}`} position={pos}></Marker>
                        )
                    }
                }
                } */}
                {/* {test} */}
            </MapContainer>
        );
    }

    // protected addGrid() {
    //     this.hexagonGrid?.push(<Hexagon center={MAP_CENTER} radius={}/>)
    // }

    protected addSingleMarker(e: any) {
        let temp = this.state.markers;
        if (!temp) {
            temp = [e.latlng];
        }
        else {
            temp.push(e.latlng);
        }
        this.setState({ markers: temp })
    }
}

export default DKMap;