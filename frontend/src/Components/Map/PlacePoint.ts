import L, { LatLng, LeafletMouseEvent } from "leaflet";
import { useMapEvents } from "react-leaflet";

interface ClickMapProps {
    ignoreLayers: L.Layer[];
    points: LatLng[];
    layerGroup: L.LayerGroup;
    addPoint: (pos: LatLng) => void;
    clearPoints: () => void;
    markerIcon: L.DivIcon;
}


export default function ClickMap(props: ClickMapProps) {
    
    const map = useMapEvents({
        click: (event) => {
            if (props.points.length < 2 && props.ignoreLayers.length < 1) {
                addMarker(event);
            }
            else {
                clearMarkers();
            }
        }
    });

    if(!map.hasLayer(props.layerGroup)) {
        map.addLayer(props.layerGroup);
    }

    function addMarker(e: LeafletMouseEvent) {
        let position: LatLng = new LatLng(e.latlng.lat, e.latlng.lng);
        props.layerGroup.addLayer(L.marker(position, {icon: props.markerIcon}).bindPopup("Lat: " + position.lat + " Lng: " + position.lng));
        props.addPoint(position);
    }

    function clearMarkers() {
        props.layerGroup.clearLayers();
        props.clearPoints();
    }
    return null;
}