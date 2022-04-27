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

    protected dividerIndex: number;
    protected checkBoxSetting: boolean;
    protected appliedFilter: boolean;

    constructor(props: ShipFilterProps) {
        super(props);
        this.dividerIndex = 0;
        this.appliedFilter = false;
        this.checkBoxSetting = true;

        this.state = {
            preApply: [],
            shipTypes: null,
            openOnUi: false,
        }
    }

    componentDidMount() {
        if(!this.state.shipTypes) {
            this.fetchShipTypes();
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
        let col1 = null;
        let col2 = null;
        if(this.state.shipTypes && this.state.shipTypes.length > 0) {
            this.dividerIndex = Math.floor(this.state.shipTypes.length * 0.5);
            col1 = (
                this.state.shipTypes.map((val, key) => {
                    if (key > this.dividerIndex) {
                        return null;
                    }
                    return (
                        <li key={key}>
                            {val.type}
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
                        </li>
                    )
                })
            );
            col2 = (
                this.state.shipTypes.map((val, key) => {
                    if (key <= this.dividerIndex) {
                        return null;
                    }
                    return (
                        <li key={key}>
                            {val.type}
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
                        </li>
                    )
                })
            )
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
                    <ul className="text-3">
                        {col1}
                    </ul>
                    <ul className="text-3">
                        {col2}
                    </ul>
                </div>
            </div>
        )
    }

    public apply() {
        if (this.state.shipTypes) {
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
        if(!isSimilar) {
            this.props.hasChanged(true);
        }
        else if (isSimilar) {
            this.props.hasChanged(false);
        }
    }

    protected async fetchShipTypes() {
        // let testArr: ShipType[] = [];
        // let testArr2: boolean[] = [];
        // for (let i = 0; i < 13; i++) {
        //     testArr.push({type: ("test"+i), checked: true});
        //     testArr2.push(true);
        // }
        // // console.log(testArr)
        // // console.log(testArr2)
        // this.setState({shipTypes: testArr, preApply: testArr2}); //FOR TESTING ONLY

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
                // console.log(data)
                if(data.length < 1) return;
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