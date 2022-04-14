import React from 'react';
import './ETATrips.css';
import { ETA } from '../../App';


interface ETATripsProps {
    tripETAs: ETA[];
    findRouteClicked: boolean;
    clearClicked: () => void;
}
 
interface ETATripsState {
    tripChosen: ETA | null;
    cleared: boolean;
}
 
export class ETATrips extends React.Component<ETATripsProps, ETATripsState> {

    protected dividerIndex: number;
    protected tripsCol1: any;
    protected tripsCol2: any;

    constructor(props: ETATripsProps) {
        super(props);
        this.dividerIndex = Math.floor(this.props.tripETAs.length * 0.5);
        this.fillColumns();
        this.state = {
            tripChosen: null,
            cleared: false,
        }
    }

    render() { 
        // let backButton = null;
        // if(this.state.tripChosen) {
        //     backButton = (
        //         <button
        //             className='eta-button eta-button-back'
        //             onClick={() => {
        //                 this.setState({tripChosen: null});
        //             }}
        //         >
        //             Back
        //         </button>
        //     );
        // }
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
                className={this.state.cleared ? "eta-container" : "eta-container-open"}
            >
                <div className='eta-header'>
                    <p className='text-1'>{this.state.tripChosen ? ("Trip ID " + this.state.tripChosen.tripId + ":") : "Trips found:"}</p>
                </div>
                {body}
                <div className='eta-footer'>
                    <button
                        className='eta-button'
                        onClick={() => {
                            this.props.clearClicked();
                            this.setState({cleared: !this.state.cleared});
                        }}
                    >
                        Clear
                    </button>
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
        this.tripsCol1 = this.props.tripETAs.map((trip, key) => {
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
        this.tripsCol2 = this.props.tripETAs.map((trip, key) => {
            if(key <= this.dividerIndex) {
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