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
import vizualizeData from "./newCSVFile.json"


interface DKMapProps {

}

interface DKMapStates {
    markers: LatLngExpression[] | null;
}

const MAP_CENTER: LatLng = new LatLng(55.8581, 9.8476);
const MAP_BOUNDS: LatLngBoundsExpression = [[58.5, 3.2], [53.5, 16.5]];
const response = window.fetch('http://127.0.0.1:8008/map_bounds');

console.log(response);

export class DKMap extends React.Component<DKMapProps, DKMapStates> {
    
    protected hexagonGrid: Hexagon[] | null;
    
    constructor(props: DKMapProps) {
        super(props);
        this.hexagonGrid = null;
        this.state = {
            markers: null
        }
    }


    render() {
        let DefaultIcon = L.icon({
            iconUrl: icon,
            shadowUrl: iconShadow
        });
        L.Marker.prototype.options.icon = DefaultIcon;
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
                className="map-container"
                center={MAP_CENTER}
                bounds={MAP_BOUNDS}
                zoom={7}
                minZoom={7}
                maxZoom={12}
                scrollWheelZoom={true}
                onClick={(e: any) => this.addSingleMarker(e)}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    bounds={MAP_BOUNDS}
                />

                {vizualizeData.map(data => (
                    <Marker
                    key={data.FIELD1}
                    position={[data.latitude, data.longitude]}>
                    </Marker>
                ))

                }


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