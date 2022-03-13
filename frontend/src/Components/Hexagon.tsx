import React from 'react';
import { Polygon, Polyline } from 'react-leaflet';    
import '../Leaflet.css';
import L, { LatLngBoundsExpression, LatLngExpression, LatLng, Icon } from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

interface HexagonProps {
    rad: number;
    center: LatLng;
}
interface HexagonStates {

}

const MAP_BOUNDS: LatLngBoundsExpression = [[58.5, 3.2], [53.5, 16.5]];

export class Hexagon extends React.Component<HexagonProps, HexagonStates> {

    protected latRat: number;
    protected lngRat: number;
    protected center: LatLng;
    protected radius: number;

    constructor(props: HexagonProps) {
        super(props);
        this.latRat = 1/11100;
        this.lngRat = 1/6600;
        this.radius = this.props.rad;
        this.center = this.props.center;
    }
    


    render() {
        let DefaultIcon = L.icon({
            iconUrl: icon,
            shadowUrl: iconShadow
        });
        L.Marker.prototype.options.icon = DefaultIcon;

        let hexPoints = this.calcHexGrid();
        
        return (       
            <Polygon positions={hexPoints} opacity={0.2}></Polygon>
        );
    }

    protected calcHexGrid() {
        // const MAP_BOUNDS: LatLngBoundsExpression = [[58.577361, 4.637123], [53.2149, 14.5386]];
        let center = new LatLng(58.5, 3.2);
        let distToNewHexCenter = this.radius * this.latRat * Math.sqrt(3);
        let distToNewHexCenter2 = this.radius *this.lngRat* 3;
        let offsetX = this.radius * this.latRat * 0.8659;
        let offsetY = this.radius * this.lngRat * 1.5000; 

        let a = 64;
        let b = 50;
        
        let hexagons = [];
        for(let i = 0; i < a; i++) {
            for(let j = 0; j < b; j++) {
                hexagons.push(this.calcHexagon(new LatLng((center.lat - (i*distToNewHexCenter)), (center.lng + (j*distToNewHexCenter2)))));
            }
        }
        for(let i = 0; i < a; i++) {
            for(let j = 0; j < b; j++) {
                hexagons.push(this.calcHexagon(new LatLng((center.lat - (i*distToNewHexCenter + offsetX)), (center.lng + (j*distToNewHexCenter2 + offsetY)))));
            }
        }
        return hexagons;
    }
    protected calcHexagon(center: LatLng): LatLngExpression[] {
        let hexagon = [];
        for(let i=0; i<=6; i++) {
            let corner = this.hexCorner(center, i);
            hexagon.push(corner);
        }

        return hexagon;
    }
    protected hexCorner(center: LatLng, i: number): LatLngExpression {
        var angle_deg = 60 * i;
        var angle_rad = Math.PI / 180 * angle_deg;
        let x = center.lat + (this.props.rad * this.latRat) * Math.sin(angle_rad);
        let y = center.lng + (this.props.rad * this.lngRat) * Math.cos(angle_rad);
        let point: LatLngExpression = [x, y];

        return point;
    }
}

export default Hexagon;