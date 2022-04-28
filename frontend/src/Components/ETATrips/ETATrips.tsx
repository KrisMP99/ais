import React from 'react';
import './ETATrips.css';
import { Trip } from '../../App';
import '../../App.css';

interface ETATripsProps {
    trips: Trip[];
    tripsShown: number;
    returnTripIndex: (fromIndex: number, amount: number) => void;
    selectedTripId: number | null;
    retSelectedTripId: (tripId: number) => void;
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
            tripChosen: this.findTripInList(),
            startIndexTripsShown: 0,
        }
    }

    componentDidUpdate(prevProps: ETATripsProps){
        if(prevProps.selectedTripId !== this.props.selectedTripId) {
            if(this.props.selectedTripId) {
                let trip = this.props.trips.find((trip) => trip.tripId === this.props.selectedTripId);
                if(trip) {
                    this.setState({tripChosen: trip});
                }
            }
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
                <div className='text-3' style={{display: "flex", flexWrap: "wrap"}}>
                    <p className='data'><strong>Trip ID:</strong> {this.state.tripChosen.tripId}</p>
                    <p className='data'><strong>ETA:</strong> {this.state.tripChosen.eta}</p>
                    <p className='data'><strong>MMSI:</strong> {this.state.tripChosen.mmsi || "undefined"}</p>
                    <p className='data'><strong>IMO:</strong> {this.state.tripChosen.imo || "undefined"}</p>
                    <p className='data'><strong>Ship type:</strong> {this.state.tripChosen.shipType || "undefined"}</p>
                    <p className='data'><strong>Type of mobile (class):</strong> {this.state.tripChosen.typeOfMobile || "undefined"}</p>
                    <p className='data'><strong>Length (m):</strong> {this.state.tripChosen.length || "undefined"}</p>
                    <p className='data'><strong>Width (m):</strong> {this.state.tripChosen.width || "undefined"}</p>
                    <p className='data'><strong>Name:</strong> {this.state.tripChosen.name || "undefined"}</p>
                </div>
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
                        this.props.retSelectedTripId(trip.tripId);
                    }}
                >
                    <label style={{ cursor: 'pointer' }}>
                        <div className='text-oneline'>
                            <p
                                className='text-3 filter-text'
                                style={{ color: trip.color, marginRight: '5px', flexGrow: 1 }}
                            >
                                <b>{trip.tripId}:</b>
                            </p>
                            <p className='text-3 filter-text'>Time: {trip.eta}</p>
                        </div>
                    </label>
                </button>
            );
        });
    }

    protected findTripInList() : Trip | null {
        if(this.props.selectedTripId) {
            let trip = this.props.trips.find((trip) => trip.tripId === this.props.selectedTripId);
            if (trip !== undefined) {
                return trip;
            }
        }
        return null;
    }
}


export default ETATrips;