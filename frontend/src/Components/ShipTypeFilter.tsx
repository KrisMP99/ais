import React from "react"
import '../App.css';

interface ShipFilterProps {
    shipType: string;
}

// To-do list
    // When a box is clicked, it should make a POST request to the API and fetch all the data 
    // After the post request


export class ShipTypeFilter extends React.Component<ShipFilterProps>{
    render() {
        return (
            <div className="align-filter-options">
                <div className="leftCheckBoxContainer">
                    <ul className="ul liLeft">
                        <li>Tanker<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Fishing<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Passenger<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Cargo<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Dredging<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Tug<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>HSC<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Reserved<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Military<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                    </ul>
                </div>

                <div className="verticalLine" />

                <div className="rightCheckBoxContainer">
                    <ul className="ul liRight">
                        <li>Law Enforcement<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Sailing<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Towing<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Pleasure<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Diving<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>SAR<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Pilot<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Undefined<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Towing long/wide<input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                        <li>Other <input type={"checkbox"} onClick={(e) => this.postShipType(this.props.shipType)}></input></li>
                    </ul>
                </div>
            </div>
        )
    }

    // https://fastapi.tiangolo.com/tutorial/body/

    protected async postShipType(shipType: string) {
        if (shipType !== " ") {
            return;
        } 

        const componentDidMount = {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'x-token': process.env.REACT_APP_TOKEN!,
            },
            body:
                JSON.stringify(
                    {
                        "ship-type": {
                            shipType
                        }
                    }
                )
        };

        // Går ud fra Trips indeholder noget med skibs typen
        fetch('http://' + process.env.REACT_APP_API! + '/trips', componentDidMount)
        .then((response) => {
            if(!response.ok){
                return null;
            } 
            else return response.json();
          })
      };
}

export default ShipTypeFilter;