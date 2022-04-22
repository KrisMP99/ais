import React from "react";
import './DateRangeFilter.css';
import '../ShipTypeFilter/ShipTypeFilter.css';
import '../../../App.css';
import '../Filters.css';
import DateRangePicker from "react-daterange-picker";
import { DatePicker, addMonths } from "@fluentui/react";




interface DateRangeFilterProps {
    hasChanged: (hasChanged: boolean) => void;
}
 
interface DateRangeFilterStates {
    openOnUi: boolean;
    startDate: Date | null | undefined;
    endDate: Date | null | undefined;
}
 
class DateFilter extends React.Component<DateRangeFilterProps, DateRangeFilterStates> {

    protected maxDate: Date;
    protected minDate: Date;

    constructor(props: DateRangeFilterProps) {
        super(props);
        this.maxDate = new Date(Date.now());
        this.minDate = new Date(addMonths(this.maxDate, -2));
        this.state = {
            openOnUi: true,
            startDate: null,
            endDate: null,
        }
    }
    render() { 
        let openSymbol = this.state.openOnUi ? "˅" : "˄";
        return ( 
            <div className="filter-container">
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                    <p className="text-2 filter-header-text"><strong>Date filter</strong></p>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                </button>
                <div className="filter-date-range-body" style={{display: (this.state.openOnUi ? '' : 'none')}}>
                    <DatePicker 
                        label="From date"
                        value={this.state.startDate!}
                        maxDate={this.maxDate}
                        minDate={this.minDate}
                    />
                    <DatePicker 
                        label="To date"
                        disabled={this.state.startDate ? true : false}
                        value={this.state.endDate!}
                        maxDate={this.maxDate}
                        minDate={this.state.startDate!}
                    />
                </div>
            </div>
         );
    }

    public apply() {

    }
}
 
export default DateFilter;