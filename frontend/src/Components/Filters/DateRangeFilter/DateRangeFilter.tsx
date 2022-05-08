import React from "react";
import './DateRangeFilter.css';
import '../ShipTypeFilter/ShipTypeFilter.css';
import '../../../App.css';
import '../Filters.css';
import { DatePicker, addMonths, DefaultButton } from "@fluentui/react";

interface DateRangeFilterProps {
    hasChanged: (hasChanged: boolean) => void;
    returnDateRange: (dates: Date[]) => void;
}
 
interface DateRangeFilterStates {
    openOnUi: boolean;
    startDate: Date | null | undefined;
    endDate: Date | null | undefined;
    minDate: Date | null;
    maxDate: Date | null;

    preApplyStartDate: Date | null | undefined;
    preApplyEndDate: Date | null | undefined;
}
 
class DateRangeFilter extends React.Component<DateRangeFilterProps, DateRangeFilterStates> {


    constructor(props: DateRangeFilterProps) {
        super(props);
        this.state = {
            openOnUi: false,
            minDate: null,
            maxDate: null,
            startDate: null,
            endDate: null,
            preApplyStartDate: null,
            preApplyEndDate: null,
        }
    }

    componentDidMount() {
        if(!this.state.minDate || !this.state.maxDate) {
            this.fetchDateInterval();
        }
    }

    componentDidUpdate(prevProps: DateRangeFilterProps, prevStates: DateRangeFilterStates) {
        if(prevStates.endDate !== this.state.endDate || prevStates.startDate !== this.state.startDate){
            this.areSimilar();
        }
    }

    render() { 
        let openSymbol = this.state.openOnUi ? "˄" : "˅";
        return ( 
            <div className="filter-container">
                <button className="filter-header" onClick={() => {this.setState({openOnUi: !this.state.openOnUi})}}>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                    <p className="text-2 filter-header-text"><strong>Date range</strong></p>
                    <p className="filter-header-arrow"><strong>{openSymbol}</strong></p>
                </button>
                <div className="filter-date-range-body" style={{display: (this.state.openOnUi ? '' : 'none')}}>
                    <div className="date-container">
                        <DatePicker 
                            className="date-picker"
                            label="From date"
                            value={this.state.startDate!}
                            disabled={this.state.minDate === new Date(Date.now())}
                            maxDate={this.state.maxDate || new Date(Date.now())}
                            minDate={this.state.minDate || new Date(Date.now())}
                            onSelectDate={(dateChosen) => {
                                if (this.state.endDate && dateChosen && dateChosen > this.state.endDate) {
                                    this.setState({startDate: dateChosen, endDate: dateChosen})
                                }
                                else {
                                    this.setState({startDate: dateChosen});
                                }
                                this.areSimilar();
                            }}
                        />
                        <DefaultButton
                            className="date-clear-button"
                            disabled={!this.dateIsDefined(this.state.startDate)}
                            onClick={() => this.setState({startDate: null, endDate: null})}
                        >
                            Clear
                        </DefaultButton>
                    </div>
                    <div className="date-container">
                        <DatePicker 
                            className="date-picker"
                            label="To date"
                            disabled={!this.dateIsDefined(this.state.startDate) || this.state.minDate === new Date(Date.now())}
                            value={this.state.endDate!}
                            maxDate={this.state.maxDate || new Date(Date.now())}
                            minDate={this.state.startDate!}
                            onSelectDate={(dateChosen) => {
                                this.setState({endDate: dateChosen});
                                this.areSimilar();
                            }}
                        />
                        <DefaultButton
                            className="date-clear-button"
                            disabled={(!this.dateIsDefined(this.state.startDate) || !this.dateIsDefined(this.state.endDate))}
                            onClick={() => this.setState({endDate: null})}
                        >
                            Clear
                        </DefaultButton>
                    </div>
                </div>
            </div>
         );
    }

    public apply() {
        if (this.dateIsDefined(this.state.endDate) && this.dateIsDefined(this.state.startDate)) {
            this.props.returnDateRange(new Array(this.state.startDate!, this.state.endDate!));
            this.setState({
                preApplyStartDate: this.state.startDate,
                preApplyEndDate: this.state.endDate,
            });
        }
        else {
            this.props.returnDateRange(new Array(this.state.minDate!, this.state.maxDate!));
            this.setState({
                startDate: null, 
                endDate: null, 
                preApplyStartDate: null, 
                preApplyEndDate: null
            });
        }
    }
    protected dateIsDefined(val: Date | null | undefined): boolean {
        return (val !== null && val !== undefined);
    }
    protected areSimilar() { 
        let endDateSame = this.state.endDate?.toDateString() === this.state.preApplyEndDate?.toDateString();
        let startDateSame = this.state.startDate?.toDateString() === this.state.preApplyStartDate?.toDateString();
        if (this.dateIsDefined(this.state.startDate) && this.dateIsDefined(this.state.endDate)) {
            if (!endDateSame || !startDateSame) {
                this.props.hasChanged(true);
            }
            else {
                this.props.hasChanged(false);
            }
        }
        else {
            this.props.hasChanged(false);
        }
    }

    protected async fetchDateInterval() {
        const requestOptions = {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'x-token': process.env.REACT_APP_TOKEN!,
            }
        };
        await fetch('http://' + process.env.REACT_APP_API! + '/date_data/dates', requestOptions)
        .then((response) => {
                if (!response.ok) {
                    return null;
                }
                return response.json();
        })
        .then((data: Date[]) => {
                if(data.length < 2 || !data) return;
                this.setState({
                    minDate: data[0],
                    maxDate: data[1],
                    startDate: data[0],
                    endDate: data[1],
                    preApplyStartDate: data[0],
                    preApplyEndDate: data[1] 
                });
                return;
        });    
    }
}
 
export default DateRangeFilter;