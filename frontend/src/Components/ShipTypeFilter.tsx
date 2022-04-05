import React from "react"
import '../App.css';

interface ShipFilterProps {
    returnShipType: (shipType: string) => void;
}

interface ShipFilterStates {
    shipTypes: string[];
}

export class ShipTypeFilter extends React.Component<ShipFilterProps, ShipFilterStates>{
    protected s: number;
    constructor(props: ShipFilterProps) {
        super(props);
        this.s = 0;
        this.state = {
            shipTypes: []
        }
    }

    render() {
        if(!this.s) {
            this.fetchShipTypes();
        }
        return (
            <div className="align-filter-options">
                <ul>
                    {this.state.shipTypes.map((val, key) => {
                        return <li key={key}>{val}<input type={"checkbox"} onClick={(e) => this.props.returnShipType(val)}></input></li>
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

        fetch('http://' + process.env.REACT_APP_API! + '/ship_attributes/ship-types', requestOptions)
            .then(async response => {
                const data = await response.json();
                if (!response.ok) {
                    return null;
                }
                return this.setState({ shipTypes: data })
            })
        this.s += 1;
    };
}

export default ShipTypeFilter;