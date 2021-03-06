import L, { LatLng, LeafletMouseEvent } from "leaflet";
import { useMapEvents } from "react-leaflet";

interface MapEventsProps {
    retMouseCoords: (pos: string[]) => void;
    ignoreLayers: L.Layer[];
    points: LatLng[];
    layerGroup: L.LayerGroup;
    addPoint: (pos: LatLng) => void;
    clearPoints: () => void;
    // markerIcon: L.DivIcon;
}


export default function MapEvents(props: MapEventsProps) {
    
    const map = useMapEvents({
        mousemove: (event) => {
            props.retMouseCoords([event.latlng.lat.toFixed(4), event.latlng.lng.toFixed(4)]);
        },
        click: (event) => {
            if (props.points.length < 2 && props.ignoreLayers.length < 1) {
                addMarker(event);
            }
        }
    });

    if(!map.hasLayer(props.layerGroup)) {
        map.addLayer(props.layerGroup);
    }

    function addMarker(e: LeafletMouseEvent) {
        if (props.points.length < 2) {
            let position: LatLng = new LatLng(e.latlng.lat, e.latlng.lng);
            // props.layerGroup.addLayer(L.marker(position, {icon: props.markerIcon}).bindPopup("Lat: " + position.lat + " Lng: " + position.lng));
            props.addPoint(position);
        }
    }
    return null;
}