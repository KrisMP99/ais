import React from "react"
import '../App.css';
import './ShipTypeFilter.css';

interface ShipFilterProps {
    returnShipType: (shipType: string) => void;
}

interface ShipFilterStates {
    shipTypes: string[];
}

export class ShipTypeFilter extends React.Component<ShipFilterProps, ShipFilterStates>{
    
    protected fireOnce: boolean;
    protected dividerIndex: number;

    constructor(props: ShipFilterProps) {
        super(props);
        this.fireOnce = false;
        this.dividerIndex = 0;
        this.state = {
            shipTypes: []
        }
    }

    render() {
        if(!this.fireOnce) {
            this.fetchShipTypes();
        }
        return (
            <div className="align-filter-options">
                <ul className="text-3">
                    {this.state.shipTypes.map((val, key) => {
                        if(key > this.dividerIndex) {
                            return;
                        }
                        return (
                            <li key={key}>
                                {val}
                                <input className="checkbox" type={"checkbox"} onClick={(e) => this.props.returnShipType(val)}/>
                            </li>
                        )
                    })}
                </ul>
                <ul className="text-3">
                    {this.state.shipTypes.map((val, key) => {
                        if(key <= this.dividerIndex) {
                            return;
                        }
                        return (
                            <li key={key}>
                                {val}
                                <input className="checkbox" type={"checkbox"} onClick={(e) => this.props.returnShipType(val)}/>
                            </li>
                        )
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
                this.dividerIndex = Math.floor(data.length * 0.5);
                console.log(this.dividerIndex);
                return this.setState({ shipTypes: data })
            });
        this.fireOnce = true;   
    };
}

export default ShipTypeFilter;