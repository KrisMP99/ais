import React from 'react';
import './ETATrips.css';
import { Trip } from '../../App';


interface ETATripsProps {
    trips: Trip[];
}
 
interface ETATripsState {
    tripChosen: Trip | null;
}
 
export class ETATrips extends React.Component<ETATripsProps, ETATripsState> {

    protected dividerIndex: number;
    protected tripsCol1: any;
    protected tripsCol2: any;

    constructor(props: ETATripsProps) {
        super(props);
        this.dividerIndex = Math.max(Math.floor(this.props.trips.length * 0.5), 20); //Handles so that it shows maximum 20 in each column
        this.fillColumns();
        this.state = {
            tripChosen: null
        }
    }

    render() { 
        let tripLengthCheck: boolean = this.props.trips.length === 0;

        let body = null;
        if(!this.state.tripChosen) {
            body = (
                <div className='eta-body'>
                    <div className='body-column'>
                        {this.tripsCol1}
                    </div>
                    <div className='body-column'>
                        {this.tripsCol2}
                    </div>
                </div>
            );
        }
        else {
            body = (
                <p>
                    ID {this.state.tripChosen.tripId} takes approximately {this.state.tripChosen.totalTime} 
                </p>
            );
        }

        return (
            <div 
                className={tripLengthCheck ? "eta-container" : "eta-container-open"}
            >
                <div className='eta-header'>
                    <p className='text-1'>{this.state.tripChosen ? ("Trip ID " + this.state.tripChosen.tripId + ":") : "Trips found:"}</p>
                </div>
                {body}
                <div className='eta-footer'>
                    <button
                        className='eta-button eta-button-back'
                        style={{display: (this.state.tripChosen ? '' : 'none')}}
                        onClick={() => {
                            this.setState({tripChosen: null});
                        }}
                    >
                        Back
                    </button>
                </div>
            </div>
        );
    }


    protected fillColumns() {
        this.tripsCol1 = this.props.trips.map((trip, key) => {
            if(key > this.dividerIndex) {
                return;
            }
            return (
                <button 
                    key={key} 
                    className='trip-button'
                    onClick={() => {
                        this.setState({tripChosen: trip});
                    }}
                >
                    <label style={{cursor: 'pointer'}}>
                        <div className='text-oneline'>
                            <p 
                                className='text-3'
                                style={{color: trip.color, marginRight: '5px'}}
                            >
                                ID {trip.tripId}: 
                            </p>
                            <p className='text-3'>Time: {trip.totalTime}</p>
                        </div>
                    </label>
                </button>
            );
        });
        this.tripsCol2 = this.props.trips.map((trip, key) => {
            if(key <= this.dividerIndex) {
                return;
            }
            else if (key > this.dividerIndex*2) {
                return;
            }
            return (
                <button 
                    key={key} 
                    className='trip-button'
                    onClick={() => {
                        this.setState({tripChosen: trip});
                    }}
                >
                    <label style={{cursor: 'pointer'}}>
                        <div className='text-oneline'>
                            <p 
                                className='text-3'
                                style={{color: trip.color, marginRight: '5px'}}
                            >
                                ID {trip.tripId}: 
                            </p>
                            <p className='text-3'>Time: {trip.totalTime}</p>
                        </div>
                    </label>
                </button>
            );
        });
    }
}

 
export default ETATrips;