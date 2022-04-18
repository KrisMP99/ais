import React from 'react';
import './ETATrips.css';
import { Trip } from '../../App';


interface ETATripsProps {
    trips: Trip[];
    tripsShown: number;
}

interface ETATripsState {
    tripChosen: Trip | null;
    startIndexTripsShown: number;
}

export class ETATrips extends React.Component<ETATripsProps, ETATripsState> {

    protected tripsDisplayed: any;

    constructor(props: ETATripsProps) {
        super(props);
        this.state = {
            tripChosen: null,
            startIndexTripsShown: 0,
        }
    }

    render() {
        let noTripsCheck: boolean = this.props.trips.length === 0;
        this.fillTripList();

        let body = null;
        let footer = null;
        let header = null;
        if (!this.state.tripChosen && !noTripsCheck) {
            body = (
                <div className='eta-body'>
                    {this.tripsDisplayed}
                </div>
            );
            footer = (
                <div className='footer'>
                    <button
                        className='button button-shift'
                        style={{ display: (this.tripsDisplayed.length > 0 ? '' : 'none') }}
                        disabled={this.state.startIndexTripsShown === 0}
                        onClick={() => {
                            this.setState({
                                startIndexTripsShown: (
                                    this.state.startIndexTripsShown > this.props.tripsShown ?
                                        this.state.startIndexTripsShown - this.props.tripsShown :
                                        0)
                            });
                        }}
                    >
                        ˄
                    </button>
                    <button
                        className='button button-shift'
                        disabled={this.tripsDisplayed.length !== this.props.tripsShown}
                        onClick={() => {
                            this.setState({ startIndexTripsShown: this.state.startIndexTripsShown + this.props.tripsShown });
                        }}
                    >
                        ˅
                    </button>
                </div>
            );
        }
        else if (this.state.tripChosen !== null) {
            body = (
                <p>
                    ID {this.state.tripChosen.tripId} takes approximately {this.state.tripChosen.totalTime}
                </p>
            );
            footer = (
                <div className='footer'>
                    <button
                        className='button button-back'
                        onClick={() => {
                            this.setState({ tripChosen: null });
                        }}
                    >
                        Back
                    </button>
                </div>
            );
        }

        if (noTripsCheck || this.props.trips.length === 0) {
            header = 'No trips found!';
            body = (
                <p className='text-2'>
                    Pick 2 points and press <b>'Find route'</b>
                </p>
            )
        }
        else {
            header = (this.state.tripChosen ? ("Trip ID " + this.state.tripChosen.tripId + ":") : "Trips found:");
        }


        return (
            <div
                className={noTripsCheck ? "eta-container" : "eta-container-open"}
            >
                <p className='text-1'>{header}</p>
                {body}
                {footer}
            </div>
        );
    }


    protected fillTripList() {
        this.tripsDisplayed = [];
        let temp: Trip[] = [];
        let i = this.state.startIndexTripsShown;
        let maxShowIndex = this.state.startIndexTripsShown + this.props.tripsShown;
        for (i; i < maxShowIndex; i++) {
            if (this.props.trips.length <= i) {
                break;
            }
            if (i <= maxShowIndex) {
                temp.push(this.props.trips[i]);
            }
        }

        this.tripsDisplayed = temp.map((trip, key) => {
            return (
                <button
                    key={key}
                    className='trip-button'
                    onClick={() => {
                        this.setState({ tripChosen: trip });
                    }}
                >
                    <label style={{ cursor: 'pointer' }}>
                        <div className='text-oneline'>
                            <p
                                className='text-3 filter-text'
                                style={{ color: trip.color, marginRight: '5px', flexGrow: 1 }}
                            >
                                <b>{trip.tripId + 1}:</b>
                            </p>
                            <p className='text-3 filter-text'>Time: {trip.totalTime}</p>
                        </div>
                    </label>
                </button>
            );
        });
    }
}


export default ETATrips;