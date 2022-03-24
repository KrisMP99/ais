import { LatLng } from 'leaflet';
import React from 'react'

async function postCoordinates(coordinates: LatLng[]){
    if(coordinates.length !== 2) {
        return;
    }
    const requestOptions = {
        method: 'POST',
        headers: { 
            'Accept': 'application/json', 
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
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

    fetch('http://0.0.0.0:8080/trips/trip', requestOptions)
    .then(response => response.json())
    .then(data => console.log(data))
  };

export default function PostButton(props: any){
    return (
        <div>
            <button onClick={(e) => postCoordinates(props.coords)}>Find route</button>
        </div>
    )
}