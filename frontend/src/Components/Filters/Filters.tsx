import React from "react"
import '../../App.css';
import DateRangeFilter from "./DateRangeFilter/DateRangeFilter";
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

    protected dateRangeFilterRef: React.RefObject<DateRangeFilter>;
    protected shipTypeFilterRef: React.RefObject<ShipTypeFilter>;
    
    constructor(props: FiltersProps) {
        super(props);
        this.filtersRef = React.createRef();
        this.dateRangeFilterRef = React.createRef();
        this.shipTypeFilterRef = React.createRef();
        this.dividerIndex = 0;
        this.checkBoxSetting = true;

        this.state = {
            hasChanged: [],
        }
    }

    render() {
        return (
            <div className='filter-container'>
                <p className='text-1'><b>Filters:</b></p>
                <div className="filter-body" ref={this.filtersRef}>
                    <DateRangeFilter 
                        ref={this.dateRangeFilterRef}
                        hasChanged={(hasChanged: boolean) => this.hasChanged(0, hasChanged)}
                    />
                    <ShipTypeFilter
                        ref={this.shipTypeFilterRef}
                        hasChanged={(hasChanged: boolean) => this.hasChanged(1, hasChanged)}
                    /> 
                </div>
                <div className="footer">
                    <button 
                        className="button btn-find-route"
                        disabled={this.state.hasChanged.every((val) => val === false)} 
                        onClick={() => {
                            this.shipTypeFilterRef.current?.apply();
                            this.dateRangeFilterRef.current?.apply();
                        }}   
                    >
                        Apply
                    </button>
                </div>
            </div>
        )
    }

    componentDidMount() {
        if(this.filtersRef.current) {
            for (let i = 0; i < this.filtersRef.current.childElementCount; i++) {
                this.state.hasChanged.push(false);   
            }
        }
    }



    protected hasChanged(index: number, value: boolean) {
        if(this.state.hasChanged.length >= index) {
            this.state.hasChanged[index] = value;
            this.setState({hasChanged: this.state.hasChanged});
        }
        else {
            console.error("ERROR in Filters.tsx - hasChanged function");
        }
    } 
}
    

export default Filters;