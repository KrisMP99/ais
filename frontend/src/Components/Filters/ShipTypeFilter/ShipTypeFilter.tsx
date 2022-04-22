import React from "react"
import '../../../App.css';
import './ShipTypeFilter.css';

interface ShipFilterProps {
    returnShipType: (shipTypes: string[]) => void;
}

interface ShipFilterStates {
    shipTypes: string[];
    openOnUi: boolean;
}

export class ShipTypeFilter extends React.Component<ShipFilterProps, ShipFilterStates>{

    protected fireOnce: boolean;
    protected dividerIndex: number;
    protected fetchedShipTypes: boolean;

    constructor(props: ShipFilterProps) {
        super(props);
        this.fetchedShipTypes = false;
        this.fireOnce = false;
        this.dividerIndex = 0;

        this.state = {
            shipTypes: [],
            openOnUi: true,
        }
    }

    componentDidMount() {
        if(!this.fetchedShipTypes) {
            this.fetchShipTypes();
            this.fetchedShipTypes = true;
        }
    }

    render() {
        let openSymbol = this.state.openOnUi ? "˅" : "˄";
        this.dividerIndex = Math.floor(this.state.shipTypes.length * 0.5);
        return (
            <div className='filter-container'>
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p><b>{openSymbol}</b></p>
                    <p className='text-2' style={{marginTop: "auto", marginBottom: "auto"}}><b>Ship type filter</b></p>
                    <p><b>{openSymbol}</b></p>
                </button>
                <div 
                    className="body-filter" 
                    style={{height: (this.state.openOnUi ? "auto" : 0), display: (this.state.openOnUi ? "" : "none")}}
                >
                    <ul className="text-3">
                        {/* <li>
                            Hello
                            <input className="checkbox" type={"checkbox"} defaultChecked={true} />
                        </li> */}
                        {this.state.shipTypes.map((val, key) => {
                            if (key > this.dividerIndex) {
                                return;
                            }
                            return (
                                <li key={key}>
                                    {val}
                                    <input className="checkbox" type={"checkbox"} defaultChecked={true} onClick={(e) => this.filter(val)} />
                                </li>
                            )
                        })}
                    </ul>
                    <ul className="text-3">
                        {/* <li>
                            Hello2
                            <input className="checkbox" type={"checkbox"} defaultChecked={true} />
                        </li> */}
                        {this.state.shipTypes.map((val, key) => {
                            if (key <= this.dividerIndex) {
                                return;
                            }
                            return (
                                <li key={key}>
                                    {val}
                                    <input className="checkbox" type={"checkbox"} defaultChecked={true} onClick={(e) => this.filter(val)} />
                                </li>
                            )
                        })}
                    </ul>
                </div>
                <div className="footer">
                    <button 
                        className="button btn-find-route"
                        // disabled={this.props.shipTypes === this.state.shipTypes} 
                        onClick={() => this.props.returnShipType(this.state.shipTypes)}   
                    >
                        Apply
                    </button>
                </div>
            </div>
        )
    }
    protected filter(type: string) {
        if (this.state.shipTypes.includes(type)) {
            this.state.shipTypes.splice(this.state.shipTypes.indexOf(type) + 1, 1)
            this.setState({ shipTypes: this.state.shipTypes })
            return;
        } else {
            this.state.shipTypes.push(type)
            this.setState({ shipTypes: this.state.shipTypes })
        }
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
                if (!response.ok) {
                    return null;
                }
				const data = await response.json();
                return this.setState({ shipTypes: data });
            });
    }
}
    

export default ShipTypeFilter;