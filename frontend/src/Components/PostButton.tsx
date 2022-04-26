import React from 'react';
import { LatLng } from 'leaflet';
import '../App.css';
import { GridSettingObj } from './GridSetting/GridSetting';
import { FilterObj } from './Filters/Filters';
import { Trip } from '../App';

export interface PostSetting {
	gridSetting: GridSettingObj | null;
	activeFilters: FilterObj | null;
}

interface PostButtonProps {
    coordinates: LatLng[];
    shipTypeArray: string[];
    returnTrips: (data: Trip[]) => void;
    postSetting: PostSetting | null;
}
interface PostButtonStates {

}

export class PostButton extends React.Component<PostButtonProps, PostButtonStates> {

    constructor(props: PostButtonProps) {
        super(props);
    }
    
    render() {
        return (
            <button 
                className="button btn-find-route" 
                disabled={this.props.coordinates.length < 2 || this.props.postSetting === null}
                onClick={(e) => this.postCoordinates(this.props.coordinates)}
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
        .then((data: Trip[]) => {
            if(data) {
                console.log("Data when recieved in postbutton: " + data);
                return this.props.returnTrips(data);
            }
        })
      };
}

export default PostButton;