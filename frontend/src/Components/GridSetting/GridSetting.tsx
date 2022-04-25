import React from "react";
import './GridSetting.css';
import '../../App.css';
import { ChoiceGroup, DefaultButton, Dropdown } from "@fluentui/react";

export interface GridSettingObj {
    isHexagon: boolean;
    size: number;
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
            gridSetting: {isHexagon: true, size: 500},
            preApplyGridSetting: {isHexagon: true, size: 500},
        }
    }

    componentDidMount() {
        this.props.onChange(this.state.gridSetting);
    }

    componentDidUpdate(prevProps: GridSettingProps, prevStates: GridSettingStates) {
        if (prevStates.gridSetting.size !== this.state.gridSetting.size || prevStates.gridSetting.isHexagon !== this.state.gridSetting.isHexagon) {
            this.props.onChange(this.state.gridSetting);
        } 
    }

    render() { 
        let dropDownOptions = [];
        if (this.state.gridSetting.isHexagon) {
            dropDownOptions = [
                { key: 500, text: '500' },
                { key: 1000, text: '1000' },
                { key: 5000, text: '5000' },
                { key: 10000, text: '10000' },
            ];
        }
        else {
            dropDownOptions = [
                { key: 806, text: '806' },
                { key: 1612, text: '1612' },
                { key: 4030, text: '4030' },
                { key: 16120, text: '16120' },
            ];
        }
        return ( 
            <div className="setting-container">
                <p className="text-1"><strong>Grid settings:</strong></p>
                <div className="setting-body">
                    <p className="text-2" style={{margin: 0}}>Grid type:</p>
                    <div className="text-3 grid-polygon-group">
                        <div className="radio-group">
                            <input 
                                type="radio" 
                                name="polygon" 
                                checked={this.state.gridSetting.isHexagon}
                                onChange={() => {
                                    let temp: GridSettingObj = { isHexagon: true, size: 500 };
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
                                    let temp: GridSettingObj = { isHexagon: false, size: 806 };
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
                        selectedKey={this.state.gridSetting.size}
                        onChange={(e, opt) => {
                            if(opt) {
                                this.setState({gridSetting: {isHexagon: this.state.gridSetting.isHexagon, size: opt.key as number}});
                            }
                        }}
                    />
                </div>
            </div>
         );
    }
}
 
export default GridSetting;