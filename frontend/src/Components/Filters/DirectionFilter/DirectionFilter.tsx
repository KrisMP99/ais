import React from "react"
import '../../../App.css';
import './DirectionFilter.css';
import '../Filters.css';

interface DirectionFilterProps {
    hasChanged: (hasChanged: boolean) => void;
    returnDirection: (dirIsForward: boolean | null) => void;
}

interface DirectionFilterStates {
    preApply: boolean | null;
    directionIsForward: boolean | null;
    openOnUi: boolean;
}

export class DirectionFilter extends React.Component<DirectionFilterProps, DirectionFilterStates>{

    protected checkBoxSetting: boolean;
    protected appliedOnce: boolean;

    constructor(props: DirectionFilterProps) {
        super(props);
        this.checkBoxSetting = true;
        this.appliedOnce = false;

        this.state = {
            preApply: null,
            directionIsForward: null,
            openOnUi: false,
        }
    }

    componentDidUpdate(prevProps: DirectionFilterProps, prevStates: DirectionFilterStates) {
        if(this.state.directionIsForward !== prevStates.directionIsForward) {
            this.areSimilar();
        }
    }

    render() {
        let openSymbol = this.state.openOnUi ? "˄" : "˅";
        return (
            <div className='filter-container'>
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                    <p className='text-2 filter-header-text'><b>Direction</b></p>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                </button>
                <div 
                    className="body-filter" 
                    style={{display: (this.state.openOnUi ? "" : "none")}}
                >
                    <div style={{display: "flex", flexWrap: "wrap"}}>
                        <label className="type-label">
                            <p className="text-3" style={{alignSelf: "flex-start", margin: "0px"}}>Forward</p>                     
                            <input 
                                className="checkbox" 
                                type={"checkbox"} 
                                checked={this.state.directionIsForward !== false} 
                                onChange={() => {
                                    if (this.state.directionIsForward === false || this.state.directionIsForward === true) {
                                        this.setState({directionIsForward: null});
                                    }
                                    else if (this.state.directionIsForward === null) {
                                        this.setState({directionIsForward: false});
                                    }
                                }}
                            />
                        </label>
                        <label className="type-label">
                            <p className="text-3" style={{alignSelf: "flex-start", margin: "0px"}}>Backward</p>                     
                            <input 
                                className="checkbox" 
                                type={"checkbox"} 
                                checked={this.state.directionIsForward !== true} 
                                onChange={() => {
                                    if (this.state.directionIsForward === false || this.state.directionIsForward === true) {
                                        this.setState({directionIsForward: null});
                                    }
                                    else if(this.state.directionIsForward === null) {
                                        this.setState({directionIsForward: true});
                                    }
                                }}
                            />
                        </label>
                    </div>
                </div>
            </div>
        )
    }

    public apply() {
        if (!this.appliedOnce) {
            this.appliedOnce = true;
            this.props.returnDirection(null);
            return;
        }
        this.props.returnDirection(this.state.directionIsForward ); 
        this.setState({preApply: this.state.directionIsForward});
    }

    protected areSimilar() {
        let isSimilar = this.state.preApply === this.state.directionIsForward;
        this.props.hasChanged(!isSimilar);   
    }
}
    

export default DirectionFilter;