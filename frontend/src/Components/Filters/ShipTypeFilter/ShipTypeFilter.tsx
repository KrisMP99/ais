import React from "react"
import '../../../App.css';
import './ShipTypeFilter.css';

interface ShipType {
    type: string;
    checked: boolean;
}

interface ShipFilterProps {
    hasChanged: (hasChanged: boolean) => void;
    // returnShipType: (shipTypes: string[]) => void;
}

interface ShipFilterStates {
    preApply: boolean[];
    shipTypes: ShipType[];
    openOnUi: boolean;
}

export class ShipTypeFilter extends React.Component<ShipFilterProps, ShipFilterStates>{

    protected dividerIndex: number;
    protected checkBoxSetting: boolean;

    constructor(props: ShipFilterProps) {
        super(props);
        this.dividerIndex = 0;

        this.checkBoxSetting = true;

        this.state = {
            preApply: [],
            shipTypes: [],
            openOnUi: true,
        }
    }

    componentDidMount() {
        if(this.state.shipTypes.length === 0) {
            this.fetchShipTypes();
        }
    }

    render() {
        let openSymbol = this.state.openOnUi ? "˅" : "˄";

        if (this.state.shipTypes.every(s => s.checked)){
            this.checkBoxSetting = true;
        }
        else  {
            this.checkBoxSetting = false;
        }
        //Sets the columns
        let col1 = null;
        let col2 = null;
        if(this.state.shipTypes.length > 0) {
            this.dividerIndex = Math.floor(this.state.shipTypes.length * 0.5);
            col1 = (
                this.state.shipTypes.map((val, key) => {
                    if (key > this.dividerIndex) {
                        return;
                    }
                    return (
                        <li key={key}>
                            {val.type}
                            <input 
                                className="checkbox" 
                                type={"checkbox"} 
                                checked={val.checked} 
                                onChange={() => {
                                    this.state.shipTypes[key].checked = !this.state.shipTypes[key].checked;
                                    this.setState({shipTypes: this.state.shipTypes});
                                }}
                            />
                        </li>
                    )
                })
            );
            col2 = (
                this.state.shipTypes.map((val, key) => {
                    if (key <= this.dividerIndex) {
                        return;
                    }
                    return (
                        <li key={key}>
                            {val.type}
                            <input 
                                className="checkbox" 
                                type={"checkbox"} 
                                defaultChecked={val.checked} 
                                onClick={() => {
                                    this.state.shipTypes[key].checked = !this.state.shipTypes[key].checked;
                                    this.setState({shipTypes: this.state.shipTypes});
                                }}
                            />
                        </li>
                    )
                })
            )
        }

        

        return (
            <div className='filter-container'>
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p><strong>{openSymbol}</strong></p>
                    <p className='text-2' style={{marginTop: "auto", marginBottom: "auto"}}><b>Ship type filter</b></p>
                    <p><strong>{openSymbol}</strong></p>
                </button>
                <div className="check-all" style={{display: this.state.openOnUi ? 'flex' : 'none'}}>
                    <p className="text-3" style={{margin: 0, marginRight: '5px'}}><em>Check all:</em></p>
                    <input 
                        type="checkbox" 
                        className="shipCheckBoxAll" 
                        checked={this.checkBoxSetting} 
                        onChange={(e) => {
                            this.checkBoxSetting = !this.checkBoxSetting;
                            this.state.shipTypes.forEach(s => s.checked = this.checkBoxSetting)
                            this.setState({shipTypes: this.state.shipTypes});
                        }}
                    />
                </div>
                <div 
                    className="body-filter" 
                    style={{height: (this.state.openOnUi ? "auto" : 0), display: (this.state.openOnUi ? "" : "none")}}
                >
                    <ul className="text-3">
                        {col1}
                    </ul>
                    <ul className="text-3">
                        {col2}
                    </ul>
                </div>
                {/* <div className="footer">
                    <button 
                        className="button btn-find-route"
                        disabled={this.areSimilar()} 
                        onClick={() => {
                            let shipTypesChecked: string[] = [];
                            this.state.shipTypes.forEach((val) => {
                                if(val.checked) {
                                    shipTypesChecked.push(val.type);
                                }
                            });
                            this.props.returnShipType(shipTypesChecked);
                            let temp = this.state.shipTypes.map((val) => {
                                return val.checked;
                            });
                            this.setState({preApply: temp});
                        }}   
                    >
                        Apply
                    </button>
                </div> */}
            </div>
        )
    }

    protected areSimilar() {
        for (let i = 0; i < this.state.shipTypes.length; i++) {
            if(this.state.shipTypes[i].checked !== this.state.preApply[i]) {
                return false;
            }
        }
        return true;
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
            .then((response) => {
                if (!response.ok) {
                    return null;
                }
                return response.json();
            })
            .then((data: string[]) => {
                let shipTypes: ShipType[] = [];
                let pre: boolean[] = [];
                data.forEach((val) => {
                    shipTypes.push({type: val, checked: true});
                    pre.push(true);
                });
                return this.setState({shipTypes: shipTypes, preApply: pre});
            });
    }
}
    

export default ShipTypeFilter;