import React, { useState } from 'react';
import './Map.css';
import Hexagon from './Hexagon'
import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';    
import '../Leaflet.css';
import L, { LatLngBoundsExpression, LatLngExpression, LatLng} from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import vizualizeData from "./polyLineTester.json";
import vizualizeData2 from "./polyLine2.json";


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

        // Code to create a 2d array of the an JSON array of objects, this is needed because leaflet polyline component only takes 2d arays
        var json = vizualizeData;
        var done: any = [];
        // https://stackoverflow.com/questions/30825129/how-to-convert-json-array-into-javascript-2d-array
        json.forEach(function(object){
            done.push([object.latitude, object.longitude]);
        });

        var json2 = vizualizeData2;
        var done2: any = [];
        // https://stackoverflow.com/questions/30825129/how-to-convert-json-array-into-javascript-2d-array
        json2.forEach(function(object){
            done2.push([object.latitude, object.longitude]);
        });

        //function jsonArrayTo2D(json: []) {
          //  let header: [] = [],
            //    AoA = [];
            //json.forEach(obj => {
             //   Object.keys(obj).forEach(key => header.includes(key) || header.push(key))
              //  let thisRow = new Array(header.length);
               // header.forEach((col, i) => thisRow[i] = obj[col] || '')
               // AoA.push(thisRow);
            //})
           // AoA.unshift(header);
           // return AoA;
        //}

        return (
            <MapContainer
                className="map-container"
                center={MAP_CENTER}
                bounds={MAP_BOUNDS}
                zoom={7}
                minZoom={7}
                maxZoom={16}
                scrollWheelZoom={true}
                onClick={(e: any) => this.addSingleMarker(e)}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    bounds={MAP_BOUNDS}
                />
                
                {/* {vizualizeData.map(data => (
                    <Polyline
                    key={data.FIELD1}
                    weight={2}
                    positions={[[data.latitude, data.longitude]]}>
                    </Polyline>
                    
                ))} */}

                    <Polyline
                    color='red'
                    positions={done}>
                    </Polyline>
                    
                    <Polyline
                    color='green'
                    positions={done2}>
                    </Polyline>
                    

                {/* {vizualizeData.map(data2 => (
                    <Marker
                    key={data2.FIELD1}
                    position={[data2.latitude, data2.longitude]}>
                    
                    </Marker>
                    
                ))} */}
                
                
                


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