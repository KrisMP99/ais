import React from "react"
import '../../App.css';
import DateFilter from "./DateFilter/DateFilter";
import './ShipTypeFilter/ShipTypeFilter.css';
import ShipTypeFilter from "./ShipTypeFilter/ShipTypeFilter";

interface FiltersProps {
    
}

interface FiltersStates {
    hasChanged: boolean[];
}

export class Filters extends React.Component<FiltersProps, FiltersStates>{
    protected filtersRef: React.RefObject<HTMLDivElement>;

    protected dividerIndex: number;
    protected checkBoxSetting: boolean;

    constructor(props: FiltersProps) {
        super(props);
        this.filtersRef = React.createRef();
        this.dividerIndex = 0;

        this.checkBoxSetting = true;

        this.state = {
            hasChanged: [false, false],
        }
    }

    render() {
        return (
            <div className='filter-container'>
                <p className='text-1'><b>Filters:</b></p>
                <div className="filter-body" ref={this.filtersRef}>
                    <DateFilter 
                        hasChanged={(hasChanged: boolean) => {

                        }}
                    />
                    <ShipTypeFilter
                        hasChanged={(hasChanged: boolean) => {
                            
                        }}
                    /> 
                </div>
                <div className="footer">
                    <button 
                        className="button btn-find-route"
                        disabled={this.areSimilar()} 
                        onClick={() => {

                        }}   
                    >
                        Apply
                    </button>
                </div>
            </div>
        )
    }

    protected areSimilar() {
        
        return true;
    } 
}
    

export default Filters;