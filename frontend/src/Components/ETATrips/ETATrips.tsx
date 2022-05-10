import React from 'react';
import './ETATrips.css';
import { ETASummary, Trip } from '../../App';
import '../../App.css';

interface ETATripsProps {
    trips: Trip[];
    eta: ETASummary | null;
    tripsShown: number;
    returnTripIndex: (fromIndex: number, amount: number) => void;
    selectedTripId: number | null;
    retSelectedTripId: (tripId: number) => void;
    fetchedOnce: boolean;
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
            else {
                this.setState({tripChosen: null})
            }
        }
        if(prevProps.trips !== this.props.trips) {
            this.setState({startIndexTripsShown: 0});
        }
    }

    render() {
        let noTripsCheck: boolean = this.props.trips.length === 0;
        this.fillTripList();

        let body = null;
        let footer = null;
        let header = null;
        let statHeader = null;
        if(!noTripsCheck && this.props.eta) {
            statHeader = (
                <div>
                    <p className='text-1'>ETA Summary:</p>
                    <div className='text-3' style={{display: "flex", flexWrap: "wrap"}}>
                        <p className='data' style={{marginBottom: 0}}><strong>Min:</strong> {this.props.eta.min}</p>
                        <p className='data' style={{marginBottom: 0}}><strong>Max:</strong> {this.props.eta.max}</p>
                        <p className='data' style={{marginBottom: 0}}><strong>Avg:</strong> {this.props.eta.avg}</p>
                        <p className='data' style={{marginBottom: 0}}><strong>Median:</strong> {this.props.eta.median}</p>
                        <p className='data' style={{marginBottom: 0}}><strong>Trips found:</strong> {this.props.trips.length}</p>
                    </div>   
                    <div></div>              
                    <hr style={{width: "70%", marginRight: "auto", marginLeft: "auto"}}/>
                </div>
            );
        }
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
                    <p className='data'><strong>Date:</strong> {this.state.tripChosen.date ? this.dateToString(this.state.tripChosen.date) : "undefined"}</p>
                    <p className='data'><strong>MMSI:</strong> {this.state.tripChosen.mmsi || "undefined"}</p>
                    <p className='data'><strong>IMO:</strong> {this.state.tripChosen.imo || "undefined"}</p>
                    <p className='data'><strong>Name:</strong> {this.state.tripChosen.name || "undefined"}</p>
                    <p className='data'><strong>Type of mobile:</strong> {this.state.tripChosen.typeOfMobile || "undefined"}</p>
                    <p className='data'><strong>Ship type:</strong> {this.state.tripChosen.shipType || "undefined"}</p>
                    <p className='data'><strong>Navigational status:</strong> {this.state.tripChosen.navStatus || "undefined"}</p>
                    <p className='data'><strong>Length (m):</strong> {this.state.tripChosen.length || "undefined"}</p>
                    <p className='data'><strong>Width (m):</strong> {this.state.tripChosen.width || "undefined"}</p>
                    <p className='data'><strong>Direction:</strong> {this.state.tripChosen.direction || "undefined"}</p>
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

        if (this.props.fetchedOnce && (noTripsCheck || this.props.trips.length === 0)) {
            header = 'No trips found!';
            body = (
                <p className='text-2'>
                    Pick 2 points and press <b>'Find route'</b>
                </p>
            )
        }
        else {
            header = '';//(this.state.tripChosen ? ("Trip ID " + this.state.tripChosen.tripId + ":") : "");
        }


        return (
            <div>
                {statHeader}
                <div
                    className={noTripsCheck ? "eta-container" : "eta-container-open"}
                >
                    <p className='text-1'>{header}</p>
                    {body}
                    {footer}
                </div>
            </div>
        );
    }
    dateToString(date: number): string {
        let strDate = date.toString();
        return strDate.slice(0, 4) + '-' + strDate.slice(4, 6) + '-' + strDate.slice(6, 8);
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
                        this.setState({tripChosen: trip});
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
                            <p className='text-3 filter-text'>{trip.eta}</p>
                        </div>
                    </label>
                </button>
            );
        });
    }

    public clear() {
        this.setState({ tripChosen: null, startIndexTripsShown: 0})
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