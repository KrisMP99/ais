import React from 'react'

async function postCoordinates(){
    const requestOptions = {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            'X-Token':  process.env.REACT_APP_TOKEN!
        },
        body: 
            JSON.stringify({
                "p1": {
                    "lat": 3.7,
                    "long": 56.79394598
                },
                "p2":{
                    "lat": 3.25,
                    "long": 57.521407319
                }
            })
    };
    fetch('http://localhost:8008/trips/trip', requestOptions)
    .then(response => response.json())
    .then(data => console.log(data))
  };

export default function PostButton(){
    return (
        <div>
            <button onClick={postCoordinates}>Find route</button>
        </div>
    )
}