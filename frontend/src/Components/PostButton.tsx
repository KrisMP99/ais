import React from 'react';
import { LatLng } from 'leaflet';

interface PostButtonProps {
    coordinates: LatLng[];
    getData: (data: LatLng[]) => void;
}
interface PostButtonStates {

}

export class PostButton extends React.Component<PostButtonProps, PostButtonStates> {

    constructor(props: PostButtonProps) {
        super(props);
    }
    
    render() {
        return (
            <div>
                <button onClick={(e) => this.postCoordinates(this.props.coordinates)}>Find route</button>
            </div>
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
                        "lat": coordinates[0].lat
                },
                    "p2":{
                        "long": coordinates[1].lng,
                        "lat": coordinates[1].lat,
                }
            })
        };
    
        fetch('http://' + process.env.REACT_APP_API! + '/trips/trip', requestOptions)
        .then(response => response.json())
        .then(data => this.props.getData(data))
      };
}

export default PostButton;