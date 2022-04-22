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
    protected appliedFilter: boolean;

    constructor(props: ShipFilterProps) {
        super(props);
        this.dividerIndex = 0;
        this.appliedFilter = false;
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

    componentDidUpdate(prevProps: ShipFilterProps, prevStates: ShipFilterStates) {
        if(!prevStates.preApply.every((val, index) => val === this.state.preApply[index])) {
            this.areSimilar();
        }
    }

    render() {
        let openSymbol = this.state.openOnUi ? "˅" : "˄";
        
        if (this.state.shipTypes.every((val) => val.checked)){
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
                                    this.areSimilar();
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
                                checked={val.checked} 
                                onChange={() => {
                                    this.state.shipTypes[key].checked = !this.state.shipTypes[key].checked;
                                    this.setState({shipTypes: this.state.shipTypes});
                                    this.areSimilar();
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
                    <p className='text-2 filter-header-text'><b>Ship type filter</b></p>
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
                            this.state.shipTypes.forEach(s => s.checked = this.checkBoxSetting);
                            this.setState({shipTypes: this.state.shipTypes});
                            this.areSimilar();
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
        let pre: boolean[] = [];
        for (let i = 0; i < this.state.shipTypes.length; i++) {
            pre.push(this.state.shipTypes[i].checked);    
        }
        this.setState({preApply: [...pre]});
    }

    protected areSimilar() {
        let isSimilar = true;
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
        const requestOptions = {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'x-token': process.env.REACT_APP_TOKEN!,
            }
        };
        let testArr: ShipType[] = [];
        let testArr2: boolean[] = [];
        for (let i = 0; i < 13; i++) {
            testArr.push({type: ("test"+i), checked: true});
            testArr2.push(true);
        }
        this.setState({shipTypes: testArr, preApply: testArr2}); //FOR TESTING ONLY
        // fetch('http://' + process.env.REACT_APP_API! + '/ship_attributes/ship-types', requestOptions)
        //     .then((response) => {
        //         if (!response.ok) {
        //             return null;
        //         }
        //         return response.json();
        //     })
        //     .then((data: string[]) => {
        //         let shipTypes: ShipType[] = [];
        //         let pre: boolean[] = [];
        //         data.forEach((val) => {
        //             shipTypes.push({type: val, checked: true});
        //             pre.push(true);
        //         });
        //         return this.setState({shipTypes: shipTypes, preApply: pre});
        //     });
    }
}
    

export default ShipTypeFilter;