import React from "react"
import '../../App.css';
import DateRangeFilter from "./DateRangeFilter/DateRangeFilter";
import './ShipTypeFilter/ShipTypeFilter.css';
import ShipTypeFilter from "./ShipTypeFilter/ShipTypeFilter";
import NavStatusFilter from "./NavStatusFilter/NavStatusFilter";
import DirectionFilter from "./DirectionFilter/DirectionFilter";

export interface FilterObj {
    dateRange: Date[] | null;
    shipTypes: string[] | null;
    navStatuses: string[] | null;
    direction: boolean | null;
}

interface FiltersProps {
    returnFilters: (val: FilterObj) => void;
}

interface FiltersStates {
    hasChanged: boolean[];
    
}

export class Filters extends React.Component<FiltersProps, FiltersStates>{
    protected filtersRef: React.RefObject<HTMLDivElement>;

    protected dividerIndex: number;
    protected checkBoxSetting: boolean;
    protected filterActive: FilterObj;

    protected dateRangeFilterRef: React.RefObject<DateRangeFilter>;
    protected shipTypeFilterRef: React.RefObject<ShipTypeFilter>;
    protected navStatusFilterRef: React.RefObject<NavStatusFilter>;
    protected directionFilterRef: React.RefObject<DirectionFilter>;
    
    constructor(props: FiltersProps) {
        super(props);
        this.filtersRef = React.createRef();
        this.dateRangeFilterRef = React.createRef();
        this.shipTypeFilterRef = React.createRef();
        this.navStatusFilterRef = React.createRef();
        this.directionFilterRef = React.createRef();
        this.filterActive = { 
            dateRange: null, 
            shipTypes: null,
            navStatuses: null,
            direction: null 
        };
        this.dividerIndex = 0;
        this.checkBoxSetting = true;

        this.state = {
            hasChanged: [],
        }
    }

    render() {
        return (
            <div className='filters-container'>
                <p className='text-1'><b>Filters:</b></p>
                <div className="filter-body" ref={this.filtersRef}>
                    <DateRangeFilter 
                        ref={this.dateRangeFilterRef}
                        hasChanged={(hasChanged: boolean) => this.hasChanged(0, hasChanged)}
                        returnDateRange={(range: Date[]) => {
                            this.filterActive.dateRange = range;
                        }}
                    />
                    <ShipTypeFilter
                        ref={this.shipTypeFilterRef}
                        hasChanged={(hasChanged: boolean) => this.hasChanged(1, hasChanged)}
                        returnShipTypes={(shipTypes: string[] | null) => {
                            this.filterActive.shipTypes = shipTypes;
                        }}
                    /> 
                    <NavStatusFilter 
                        ref={this.navStatusFilterRef}
                        hasChanged={(hasChanged: boolean) => this.hasChanged(2, hasChanged)}
                        returnNavStatuses={(statuses: string[] | null) => {
                            this.filterActive.navStatuses = statuses;
                        }}
                    />
                    <DirectionFilter 
                        ref={this.directionFilterRef}
                        hasChanged={(hasChanged: boolean) => this.hasChanged(3, hasChanged)}
                        returnDirection={(dirIsForward: boolean | null) => {
                            this.filterActive.direction = dirIsForward;
                        }}
                    />
                </div>
                <div className="footer">
                    <button 
                        className="button btn-find-route"
                        style={{marginTop: "5px"}}
                        disabled={this.state.hasChanged.every((val) => val === false)} 
                        onClick={() => this.applyFilter()}   
                    >
                        Apply filter
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
        if(!this.filterActive.shipTypes) {
            this.applyFilter();
        }
    }

    protected applyFilter() {
        let temp: boolean[] = [];
        for (let i = 0; i < this.state.hasChanged.length; i++) {
            temp.push(false);
        }
        this.directionFilterRef.current?.apply();
        this.navStatusFilterRef.current?.apply();
        this.dateRangeFilterRef.current?.apply();
        this.shipTypeFilterRef.current?.apply();
        this.props.returnFilters(this.filterActive);
        this.setState({hasChanged: temp});
    }

    protected hasChanged(index: number, value: boolean) {
        if(this.state.hasChanged.length >= index) {
            let temp = [...this.state.hasChanged];
            temp[index] = value;
            this.setState({hasChanged: temp});
        }
        else {
            console.error("ERROR in Filters.tsx - hasChanged function");
        }
    } 
}
    

export default Filters;