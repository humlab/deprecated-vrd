import React from 'react';
import PropTypes from 'prop-types';

export default class Visualization extends React.Component {
  render() {
    return (
      <div>
        <Canvas width={640} height={480} />
      </div>
    );
  }
}

class Canvas extends React.Component {
  static defaultProps = {
    width: 320,
    height: 200,
    strokeStyle: '#F00',
    lineWidth: 1
  };

  canvas = null;
  ctx = null;

  render() {
    return (
      <canvas
        width={this.props.width}
        height={this.props.height}
        ref={c => {
          this.canvas = c;
        }}
      />
    );
  }
}

Canvas.propTypes = {
  lineWidth: PropTypes.number.isRequired,
  width: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired
};
