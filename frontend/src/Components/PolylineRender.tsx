import React from "react";
import { Polyline } from 'react-leaflet';
import { LatLng } from 'leaflet';

interface PolylineRenderProps {
    polylines: LatLng[];
}
interface PolylineRenderStates {

}

export class PolylineRender extends React.Component<PolylineRenderProps, PolylineRenderStates> {
    constructor(props: PolylineRenderProps) {
        super(props);
    }

    render(){
        return(
            <Polyline
                positions={this.props.polylines}
            />   
        );
    };

    
}

export default PolylineRender;