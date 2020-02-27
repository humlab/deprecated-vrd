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
  shouldRender = false;

  componentDidMount() {
    this.ctx = this.canvas.getContext('2d');
    this.ctx.strokeStyle = this.props.strokeStyle;
    this.ctx.lineWidth = this.props.lineWidth;

    // Perform initial render
    console.log('Component did mount: prompting initial render');
    this.shouldRender = true;
    requestAnimationFrame(this.updateCanvas);
  }

  updateCanvas = () => {
    if (!this.shouldRender) {
      return;
    }

    console.log('Clearing canvas');
    this.ctx.clearRect(0, 0, this.props.width, this.props.height);

    console.log('Rendering items to canvas');
    const rect = {
      x: 50,
      y: 50,
      w: 50,
      h: 50
    };

    this.ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
  };

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
  height: PropTypes.number.isRequired,
  strokeStyle: PropTypes.string.isRequired
};
