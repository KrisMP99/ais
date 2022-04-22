import React from "react"
import '../../../App.css';
import './ShipTypeFilter.css';

interface ShipType {
    type: string;
    checked: boolean;
}

interface ShipFilterProps {
    returnShipType: (shipTypes: string[]) => void;
}

interface ShipFilterStates {
    preApply: ShipType[];
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
            console.log("Fetching ship types...");
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
                    <input type="checkbox" className="shipCheckBoxAll" defaultChecked={this.checkBoxSetting} onChange={(e) => {
                        this.checkBoxSetting = !this.checkBoxSetting;
                        this.state.shipTypes.forEach(s => s.checked = this.checkBoxSetting)
                    }}/>
                </button>
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
                <div className="footer">
                    <button 
                        className="button btn-find-route"
                        disabled={JSON.stringify(this.state.shipTypes) === JSON.stringify(this.state.preApply)} 
                        onClick={() => {
                            let shipTypesChecked: string[] = [];
                            this.state.shipTypes.forEach((val) => {
                                if(val.checked) {
                                    shipTypesChecked.push(val.type);
                                }
                            });
                            this.props.returnShipType(shipTypesChecked);
                            this.setState({preApply: [...this.state.shipTypes]});
                        }}   
                    >
                        Apply
                    </button>
                </div>
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
            .then((response) => {
                if (!response.ok) {
                    return null;
                }
                return response.json();
            })
            .then((data: string[]) => {
                let shipTypes: ShipType[] = [];
                let pre: ShipType[] = [];
                data.forEach((val) => {
                    shipTypes.push({type: val, checked: true});
                    pre.push({type: val, checked: true});
                });
                return this.setState({shipTypes: [...shipTypes], preApply: [...pre]});
            });
    }
}
    

export default ShipTypeFilter;