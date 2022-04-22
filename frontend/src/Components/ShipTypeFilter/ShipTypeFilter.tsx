import React from "react"
import '../../App.css';
import './ShipTypeFilter.css';

interface ShipFilterProps {
    shipTypes: string[];
    returnShipType: (shipTypes: string[]) => void;
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
        this.dividerIndex = Math.floor(this.props.shipTypes.length * 0.5);

        this.state = {
            shipTypes: [],
        }
    }

    componentDidMount(){
        if (this.props.shipTypes.length > 0){
            this.setState({shipTypes: this.props.shipTypes});
        }
    }

    render() {
        return (
            <div className='filter-container'>
                <p className='text-1' style={{justifySelf: "flex-start"}}>Ship type filter</p>
                <div className="body-filter">
                    <ul className="text-3">
                        {this.state.shipTypes.map((val, key) => {
                            if (key > this.dividerIndex) {
                                return;
                            }
                            return (
                                <li key={key}>
                                    {val}
                                    <input className="checkbox" type={"checkbox"} onClick={(e) => this.filter(val)} />
                                </li>
                            )
                        })}
                    </ul>
                    <ul className="text-3">
                        {this.state.shipTypes.map((val, key) => {
                            if (key <= this.dividerIndex) {
                                return;
                            }
                            return (
                                <li key={key}>
                                    {val}
                                    <input className="checkbox" type={"checkbox"} onClick={(e) => this.filter(val)} />
                                </li>
                            )
                        })}
                    </ul>
                </div>
                <div className="footer">
                    <button 
                        className="button btn-find-route"
                        disabled={this.props.shipTypes === this.state.shipTypes} 
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
}
    

export default ShipTypeFilter;