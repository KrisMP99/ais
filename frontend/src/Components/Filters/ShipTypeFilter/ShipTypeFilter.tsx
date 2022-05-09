import React from "react"
import '../../../App.css';
import './ShipTypeFilter.css';
import '../Filters.css';

interface ShipType {
    type: string;
    checked: boolean;
}

interface ShipFilterProps {
    hasChanged: (hasChanged: boolean) => void;
    returnShipTypes: (shipTypes: string[] | null) => void;
}

interface ShipFilterStates {
    preApply: boolean[];
    shipTypes: ShipType[] | null;
    openOnUi: boolean;
}

export class ShipTypeFilter extends React.Component<ShipFilterProps, ShipFilterStates>{

    protected checkBoxSetting: boolean;
    protected appliedOnce: boolean;
    protected fetchedOnce: boolean;

    constructor(props: ShipFilterProps) {
        super(props);
        this.checkBoxSetting = true;
        this.appliedOnce = false;
        this.fetchedOnce = false;

        this.state = {
            preApply: [],
            shipTypes: null,
            openOnUi: false,
        }
    }

    componentDidMount() {
        if(!this.state.shipTypes && !this.fetchedOnce) {
            this.fetchShipTypes();
            this.fetchedOnce = true;
        }
    }

    render() {
        let openSymbol = this.state.openOnUi ? "˄" : "˅";
        
        if (this.state.shipTypes && this.state.shipTypes.every((val) => val.checked)){
            this.checkBoxSetting = true;
        }
        else  {
            this.checkBoxSetting = false;
        }
        //Sets the columns
        let shipTypes = null;
        if(this.state.shipTypes && this.state.shipTypes.length > 0) {
            shipTypes = this.state.shipTypes.map((val, key) => {
                return (
                    <label key={key} className="type-label">
                        <p className="text-3" style={{margin: "0px"}}>{val.type}</p>                     
                        <input 
                            className="checkbox" 
                            type={"checkbox"} 
                            checked={val.checked} 
                            onChange={() => {
                                if(this.state.shipTypes) {
                                    let temp = this.state.shipTypes;
                                    temp[key].checked = !temp[key].checked;
                                    this.setState({shipTypes: temp});
                                    this.areSimilar();
                                }
                            }}
                        />
                    </label>
                );
            })
        }
        return (
            <div className='filter-container'>
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                    <p className='text-2 filter-header-text'><b>Ship type</b></p>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                </button>
                <div className="check-all" style={{display: this.state.openOnUi ? 'flex' : 'none'}}>
                    <p className="text-3" style={{margin: 0, marginRight: '5px'}}><em>Check all:</em></p>
                    <input 
                        type="checkbox" 
                        className="shipCheckBoxAll" 
                        checked={this.checkBoxSetting} 
                        onChange={(e) => {
                            this.checkBoxSetting = !this.checkBoxSetting; 
                            if(this.state.shipTypes) {
                                this.state.shipTypes.forEach(s => s.checked = this.checkBoxSetting);
                                this.setState({shipTypes: this.state.shipTypes});
                                this.areSimilar();
                            }
                        }}
                    />
                </div>
                <div 
                    className="body-filter" 
                    style={{display: (this.state.openOnUi ? "" : "none")}}
                >
                    <div style={{display: "flex", flexWrap: "wrap"}}>
                        {shipTypes}
                    </div>
                </div>
            </div>
        )
    }

    public apply() {
        if (this.state.shipTypes) {
            if (!this.appliedOnce && this.state.shipTypes.every((val) => val.checked)) {
                this.appliedOnce = true;
                this.props.returnShipTypes(null);
                return;
            }
            else if (this.state.shipTypes.every((val) => val.checked)) {
                this.props.returnShipTypes(null);
                return;
            }
            let pre: boolean[] = [];
            let ret: string[] = [];
            for (let i = 0; i < this.state.shipTypes.length; i++) {
                if (this.state.shipTypes[i].checked) {
                    ret.push(this.state.shipTypes[i].type);
                }
                pre.push(this.state.shipTypes[i].checked);    
            }
            this.props.returnShipTypes(ret); 
            this.setState({preApply: [...pre]});
        }
        else {
            this.props.returnShipTypes(null);
        }
    }

    protected areSimilar() {
        let isSimilar = true;
        if(!this.state.shipTypes) {
            return;
        }
        for (let i = 0; i < this.state.shipTypes.length; i++) {
            if(this.state.shipTypes[i].checked !== this.state.preApply[i]) {
                isSimilar = false;
            }
        }
        this.props.hasChanged(!isSimilar); 
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
        let shipTypes: ShipType[] = [];
        let pre: boolean[] = [];
        fetch('http://' + process.env.REACT_APP_API! + '/ship_attributes/ship-types', requestOptions)
        .then((response) => {
                if (!response.ok) {
                    return this.setState({shipTypes: [], preApply: []});
                }
                return response.json();
        })
        .then((data: string[]) => {
                if(!data || data.length < 1) return;
                data.forEach((val) => {
                    shipTypes.push({type: val, checked: true});
                    pre.push(true);
                });
                return;
        });    
        this.setState({shipTypes: shipTypes, preApply: pre});
    }
}
    

export default ShipTypeFilter;