import React from "react"
import '../App.css';

interface ShipFilterProps {
    returnShipType: (shipType: string) => void;
}

interface ShipFilterStates {
    shipTypes: string[];
}

export class ShipTypeFilter extends React.Component<ShipFilterProps, ShipFilterStates>{

    constructor(props: ShipFilterProps) {
        super(props);
        this.state = {
            shipTypes: []
        }
    }

    render() {
        return (
            <div className="align-filter-options">
                <ul>
                    {this.state.shipTypes.map((val) => {
                        return <li>{val}<input type={"checkbox"} onClick={(e) => this.props.returnShipType(val)}></input></li>
                    })}
                </ul>
            </div>
        )
    }

    protected async fetchShipTypes() {
        const requestOptions = {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'x-token': process.env.REACT_APP_TOKEN!,
            }
        };

        fetch('http://' + process.env.REACT_APP_API! + '/trips/ship-trips', requestOptions)
            .then((response) => {
                if (!response.ok) {
                    return null;
                }
                else return response.json();
            })
            .then((data: string[]) => {
                return this.setState({ shipTypes: data });
            })
    };
}

export default ShipTypeFilter;