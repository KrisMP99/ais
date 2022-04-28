import React from 'react';
import L, { LatLng } from 'leaflet';
import '../App.css';
import { GridSettingObj } from './GridSetting/GridSetting';
import { FilterObj } from './Filters/Filters';
import { Trip } from '../App';
import { FeatureCollection } from 'geojson';
import { PostSetting } from './Map/Map';



interface PostButtonProps {
    coordinates: LatLng[];
    shipTypeArray: string[];
    returnTrips: (data: Trip[]) => void;
    postSetting: PostSetting | null;
}
interface PostButtonStates {

}

export class PostButton extends React.Component<PostButtonProps, PostButtonStates> {
    
    render() {
        return (
            <button 
                className="button btn-find-route" 
                disabled={this.props.coordinates.length < 2 || this.props.postSetting === null}
                onClick={() => this.setState({getTrips: true})}// this.postCoordinates(this.props.coordinates)}
            >
                Find route
            </button>
        )
    }

    protected async postCoordinates(coordinates: LatLng[]){
        if(coordinates.length !== 2) {
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
                        "long": coordinates[0].lng,
                        "lat": coordinates[0].lat,
                        "is_hexagon": this.props.postSetting?.gridSetting?.isHexagon,
                        "grid_size": this.props.postSetting?.gridSetting?.size
                },
                    "p2":{
                        "long": coordinates[1].lng,
                        "lat": coordinates[1].lat,
                        "is_hexagon": this.props.postSetting?.gridSetting?.isHexagon,
                        "grid_size": this.props.postSetting?.gridSetting?.size
                }
            })
        };
    
        fetch('http://' + process.env.REACT_APP_API! + '/trips', requestOptions)
        .then((response) => {
            if(!response.ok){
                return null;
            } 
            else return response.json();
          })
        // .then((data: Trip[]) => {
        //     if(data) {
        //         return this.props.returnTrips(data);
        //     }
        //     else alert('No trips were found between the two coordinates')
        // })
        .then((data: FeatureCollection) => {
            let trips: Trip[] = [];
            L.geoJSON(data, {
                onEachFeature: (feature) => {
                    trips.push({ 
                        tripId: feature.properties.trip_id,
                        eta: feature.properties.eta,
                        color: feature.properties.color,
                        shipType: feature.properties.ship_type,
                        mmsi: feature.properties.mmsi,
                        imo: feature.properties.imo,
                        typeOfMobile: feature.properties.type_of_mobile,
                        name: feature.properties.name,
                        width: feature.properties.width,
                        length: feature.properties.length
                    })
                    
                }
            })
            
            return;
        })
      };
}
// export interface Trip {
// 	trip_id: number;
// 	line_string: LatLng[]
// 	eta: string;
	// color: string;
	// ship_type: string;
	// mmsi?: number;
	// imo?: number;
	// type_of_mobile?: string;
	// name?: string;
	// width?: number;
	// length?: number;
// }
// self.trip_id = trip_id
// self.line_string = line_string
// self.eta = eta
// self.color = give_color()
// self.ship_Type = ship_type
// self.mmsi = mmsi
// self.imo = imo
// self.type_of_mobile = type_of_mobile
// self.name = name,
// self.width = width,
// self.length = length

export default PostButton;