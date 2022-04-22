import React from "react";
import './DateFilter.css';
import '../ShipTypeFilter/ShipTypeFilter.css';
import '../../../App.css';


interface DateFilterProps {
    returnDateInterval: () => void;
}
 
interface DateFilterState {
    openOnUi: boolean;
}
 
class DateFilter extends React.Component<DateFilterProps, DateFilterState> {

    constructor(props: DateFilterProps) {
        super(props);
        this.state = {
            openOnUi: true,
        }
    }
    render() { 
        let openSymbol = this.state.openOnUi ? "˅" : "˄";
        return ( 
            <div className="filter-container">
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p><b>{openSymbol}</b></p>
                    <p className='text-2' style={{marginTop: "auto", marginBottom: "auto"}}><b>Date filter</b></p>
                    <p><b>{openSymbol}</b></p>
                </button>
                {/* <ReactDatePicker
                    dateFormat={"dd-mm-yyyy"}
                    // selected={}
                    onChange={() => {}}
                >
                </ReactDatePicker> */}
            </div>
         );
    }
}
 
export default DateFilter;