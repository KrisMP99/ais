import React from "react"
import '../../../App.css';
import './NavStatusFilter.css';
import '../Filters.css';

interface NavStatus {
    type: string;
    checked: boolean;
}

interface NavStatusFilterProps {
    hasChanged: (hasChanged: boolean) => void;
    returnNavStatuses: (statuses: string[] | null) => void;
}

interface NavStatusFilterStates {
    preApply: boolean[];
    navStatuses: NavStatus[] | null;
    openOnUi: boolean;
}

export class NavStatusFilter extends React.Component<NavStatusFilterProps, NavStatusFilterStates>{

    protected checkBoxSetting: boolean;
    protected appliedOnce: boolean;

    constructor(props: NavStatusFilterProps) {
        super(props);
        this.checkBoxSetting = true;
        this.appliedOnce = false;

        this.state = {
            preApply: [],
            navStatuses: null,
            openOnUi: false,
        }
    }

    componentDidMount() {
        if(!this.state.navStatuses) {
            this.fetchNavStatuses();
        }
    }
    componentDidUpdate(prevPros: NavStatusFilterProps, prevStates: NavStatusFilterStates) {
        if(JSON.stringify(this.state.navStatuses) !== JSON.stringify(prevStates.navStatuses)) {
            this.areSimilar();
        }
    }

    render() {
        let openSymbol = this.state.openOnUi ? "˄" : "˅";
        
        if (this.state.navStatuses && this.state.navStatuses.every((val) => val.checked)){
            this.checkBoxSetting = true;
        }
        else  {
            this.checkBoxSetting = false;
        }
        //Sets the columns
        let shipTypes = null;
        if(this.state.navStatuses && this.state.navStatuses.length > 0) {
            shipTypes = this.state.navStatuses.map((val, key) => {
                return (
                    <label key={key} className="type-label">
                        {/* <li key={key}> */}
                        <p className="text-3" style={{alignSelf: "flex-start", margin: "0px"}}>{val.type}</p>                     
                        <input 
                            className="checkbox" 
                            type={"checkbox"} 
                            checked={val.checked} 
                            onChange={() => {
                                if(this.state.navStatuses) {
                                    let temp = this.state.navStatuses;
                                    temp[key].checked = !temp[key].checked;
                                    this.setState({navStatuses: temp});
                                    // this.areSimilar();
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
                    <p className='text-2 filter-header-text'><b>Navigational Status</b></p>
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
                            if(this.state.navStatuses) {
                                this.state.navStatuses.forEach(s => s.checked = this.checkBoxSetting);
                                this.setState({navStatuses: this.state.navStatuses});
                                // this.areSimilar();
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
        if (this.state.navStatuses) {
            if (!this.appliedOnce && this.state.navStatuses.every((val) => val.checked)) {
                this.appliedOnce = true;
                this.props.returnNavStatuses(null);
                return;
            }
            let pre: boolean[] = [];
            let ret: string[] = [];
            for (let i = 0; i < this.state.navStatuses.length; i++) {
                if (this.state.navStatuses[i].checked) {
                    ret.push(this.state.navStatuses[i].type);
                }
                pre.push(this.state.navStatuses[i].checked);    
            }
            this.props.returnNavStatuses(ret); 
            this.setState({preApply: [...pre]});
        }
        else {
            this.props.returnNavStatuses(null);
        }
    }

    protected areSimilar() {
        let isSimilar = true;
        if(!this.state.navStatuses) {
            return;
        }
        for (let i = 0; i < this.state.navStatuses.length; i++) {
            if(this.state.navStatuses[i].checked !== this.state.preApply[i]) {
                isSimilar = false;
            }
        }
        this.props.hasChanged(!isSimilar);
    }

    protected async fetchNavStatuses() {
        const requestOptions = {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'x-token': process.env.REACT_APP_TOKEN!,
            }
        };
        let statuses: NavStatus[] = [];
        let pre: boolean[] = [];
        await fetch('http://' + process.env.REACT_APP_API! + '/navigational_attributes/nav-attrs', requestOptions)
        .then((response) => {
                if (!response.ok) {
                    console.log("NAV STATUS RESPONSE NOT OK")
                    return this.setState({navStatuses: [], preApply: []});
                }
                return response.json();
        })
        .then((data: string[]) => {
                if(!data) return;
                data.forEach((val) => {
                    statuses.push({type: val, checked: true});
                    pre.push(true);
                });
                return;
        });    
        this.setState({navStatuses: statuses, preApply: pre});
    }
}
    

export default NavStatusFilter;