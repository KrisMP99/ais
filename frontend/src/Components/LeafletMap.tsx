import React, { useEffect } from "react";
import L, { LatLng, LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";
import { LatLngBoundsExpression } from "leaflet";
import { GeoJsonObject } from "geojson";
import { MapConsumer, useMapEvent } from "react-leaflet";
const MAP_BOUNDS: LatLngBoundsExpression = [[58.5, 3.2], [53.5, 16.5]];
const MAP_CENTER: LatLng = new LatLng(55.8581, 9.8476);

function MyComponent() {
    const map = useMapEvent('click', () => {
      console.log("hhh");
    })
    return null
  }

export default function LeafletMap() {
    useEffect(() => {
        map();
    }, []);
    const styling = {
        opacity: 0.1,
        fillOpacity: 0,
        color: "black",
    }

    const map = async () => {
        const mapSW: LatLngExpression = [58.5, 3.2];
        const mapNE: LatLngExpression = [53.5, 16.5];
        const map = L.map("map").setView(MAP_CENTER, 7);
        
        var maxBounds = L.latLngBounds(
            mapSW,
            mapNE
        );
        map.setMaxBounds(maxBounds);

        let s = await fetch('http://127.0.0.1:8008/map_bounds?access_token='+ process.env.REACT_APP_API_KEY)
        .then(res => res.json());

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:12, minZoom:7}).addTo(map);
        L.geoJSON(s, {style: styling}).addTo(map);
        // useMapEvent('click', () => {
        //     console.log("HHH");
        // })
    }

    
    return <div id="map" style={{ height: "100vh", width: "100vh" }}></div>;
}
