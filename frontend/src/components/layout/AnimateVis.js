import React from 'react';
import Visualization from './Visualization';

class AnimateVis extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
    };
    this.updateAnimationState = this.updateAnimationState.bind(this);
  }

  componentDidMount() {
    this.rAF = requestAnimationFrame(this.updateAnimationState);
  }

  updateAnimationState() {
    this.rAF = requestAnimationFrame(this.updateAnimationState);
  }

  componentWillUnmount() {
    cancelAnimationFrame(this.rAF);
  }

  render() {
    return <Visualization response={this.props.props} />;
  }
}

export default AnimateVis;
