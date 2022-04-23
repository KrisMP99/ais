import React from "react";
import './GridSetting.css';
import '../../App.css';
import { ChoiceGroup, DefaultButton, Dropdown } from "@fluentui/react";

export interface GridSettingObj {
    isHexagon: boolean;
    sizeIndex: number;
}

interface GridSettingProps {
    onChange: (settings: GridSettingObj) => void;
}
 
interface GridSettingStates {
    openOnUi: boolean;
    gridSetting: GridSettingObj;
    preApplyGridSetting: GridSettingObj;
}
 
class GridSetting extends React.Component<GridSettingProps, GridSettingStates> {

    constructor(props: GridSettingProps) {
        super(props);
        this.state = {
            openOnUi: false,
            gridSetting: {isHexagon: true, sizeIndex: 0},
            preApplyGridSetting: {isHexagon: true, sizeIndex: 0},
        }
    }

    componentDidUpdate(prevProps: GridSettingProps, prevStates: GridSettingStates) {
        
    }

    render() { 
        let openSymbol = this.state.openOnUi ? "˄" : "˅";

        let dropDownOptions = [];
        if (this.state.gridSetting.isHexagon) {
            dropDownOptions = [
                { key: 0, text: '500' },
                { key: 1, text: '1000' },
                { key: 2, text: '5000' },
                { key: 3, text: '10000' },
            ];
        }
        else {
            dropDownOptions = [
                { key: 0, text: '806' },
                { key: 1, text: '1603' },
                { key: 2, text: '6006' },
                { key: 3, text: '16203' },
            ];
        }
        return ( 
            <div className="setting-container">
                <p className="text-1"><strong>Grid settings</strong></p>
                <div className="setting-body">
                    <p className="text-2" style={{margin: 0}}>Grid type:</p>
                    <div className="text-3 grid-polygon-group">
                        <div className="radio-group">
                            <input 
                                type="radio" 
                                name="polygon" 
                                checked={this.state.gridSetting.isHexagon}
                                onChange={() => {
                                    let temp: GridSettingObj = { isHexagon: true, sizeIndex: 0 };
                                    this.props.onChange(temp);
                                    this.setState({gridSetting: temp });
                                }}
                            />
                            <p className="text-2 radio-text">Hexagon</p>
                        </div>
                        <div className="radio-group">
                            <input 
                                type="radio" 
                                name="polygon" 
                                checked={!this.state.gridSetting.isHexagon}
                                onChange={() => {
                                    let temp: GridSettingObj = { isHexagon: false, sizeIndex: 0 };
                                    this.props.onChange(temp);
                                    this.setState({gridSetting: temp });
                                }}
                            />
                            <p className="text-2 radio-text">Square</p>
                        </div>
                    </div>
                    <Dropdown 
                        className="dropdown"
                        label="Grid side length (meters):"
                        options={dropDownOptions}
                        selectedKey={this.state.gridSetting.sizeIndex}
                        onChange={(e, opt, key) => {
                            if(key) {
                                this.setState({gridSetting: {isHexagon: this.state.gridSetting.isHexagon, sizeIndex: key}});
                            }
                        }}
                    />
                </div>
            </div>
         );
    }
}
 
export default GridSetting;