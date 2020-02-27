import React from 'react';
import PropTypes from 'prop-types';

export default class Visualization extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      selected: false,
      label: '',
      x: -1,
      y: -1,
      w: -1,
      h: -1
    };
  }

  onSelected = segment => {
    this.setState({
      selected: segment !== null,
      ...segment
    });
  };

  getSelectionStr() {
    if (this.state.selected) {
      const state = this.state;
      return `label: ${state.label}, x: ${state.x}, y: ${state.y}, w: ${state.w}, h: ${state.h}`;
    }

    return 'No Selection';
  }
  render() {
    return (
      <div>
        <Canvas width={640} height={480} onSelected={this.onSelected} />
        <div>{this.getSelectionStr()}</div>
      </div>
    );
  }
}

class Canvas extends React.Component {
  static defaultProps = {
    width: 320,
    height: 200,
    strokeStyle: '#F00',
    lineWidth: 1,
    onSelected: () => {}
  };

  canvas = null;
  ctx = null;
  shouldRender = false;
  objectUnderMouse = null;

  querySegments = [
    new Segment('Query Segment 1', 50, 50, 50, 50),
    new Segment('Query Segment 2', 100, 50, 50, 50)
  ];

  referenceSegments = [
    new Segment('Reference Segment 1', 50, 250, 50, 50),
    new Segment('Reference Segment 2', 100, 250, 50, 50)
  ];

  segments = [...this.querySegments, ...this.referenceSegments];

  lines = [
    new ComparisonLine(this.querySegments[0], this.referenceSegments[1])
  ];

  curX = -1;
  curY = -1;

  componentDidMount() {
    this.ctx = this.canvas.getContext('2d');
    this.ctx.strokeStyle = this.props.strokeStyle;
    this.ctx.lineWidth = this.props.lineWidth;
    this.addMouseEvents();

    // Perform initial render
    console.log('Component did mount: prompting initial render');
    this.shouldRender = true;
    requestAnimationFrame(this.updateCanvas);
  }

  updateCanvas = () => {
    if (!this.shouldRender) {
      return;
    }

    console.log('Clearing canvas and rendering items');
    this.ctx.clearRect(0, 0, this.props.width, this.props.height);
    this.segments.map(o => o.render(this.ctx));
    this.lines.map(o => o.render(this.ctx));
  };

  componentWillUnmount() {
    this.removeMouseEvents();
  }

  addMouseEvents() {
    document.addEventListener('mousemove', this.onMouseMove, false);
  }

  removeMouseEvents() {
    document.removeEventListener('mousemove', this.onMouseMove, false);
  }

  onMouseMove = e => {
    this.curX = e.offsetX;
    this.curY = e.offsetY;

    const wasHovering = this.objectUnderMouse !== null;
    let isHovering = false;

    for (const segment of this.segments) {
      const mouseIsOverObject = segment.setIsHovered(
        this.ctx.isPointInPath(segment.path, this.curX, this.curY)
      );

      // The mouse is over an object
      if (mouseIsOverObject) {
        if (!wasHovering) {
          // We weren't hovering over anything before,
          console.log(
            `Was not hovering over anything, now hovering over ${segment.label}`
          );

          this.shouldRender = true;
          this.objectUnderMouse = segment;

          isHovering = true;
        } else if (!segment.equal(this.objectUnderMouse)) {
          // the mouse is over a different object than before,
          console.log(
            `Was hovering over ${this.objectUnderMouse.label}. Now hovering over ${segment.label}`
          );
          this.shouldRender = true;
          this.objectUnderMouse = segment;

          isHovering = true;
        } else {
          // Still hovering over the same rectangle
          this.shouldRender = false;
          isHovering = true;
        }
      }
    }

    if (wasHovering && isHovering) {
      // Segments might share x and y coordinates, with a minor overlap. We ensure that only
      // one is marked as hovered.
      const others = this.segments.filter(o => !o.equal(this.objectUnderMouse));
      others.map(o => o.setIsHovered(false));
    } else if (wasHovering && !isHovering) {
      // We couldn't find an object which we were hovering over, but we were hovering
      // before! We must re-render!
      console.log(
        `Was hovering over ${this.objectUnderMouse.label}. Now hovering over nothing`
      );
      this.shouldRender = true;
      this.objectUnderMouse = null;
    } else if (!wasHovering && !isHovering) {
      // We weren't hovering, nor are we hovering. No need to re-render
      this.shouldRender = false;
    }

    this.props.onSelected(this.objectUnderMouse);

    if (this.shouldRender) {
      requestAnimationFrame(this.updateCanvas);
    }
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
  strokeStyle: PropTypes.string.isRequired,
  onSelected: PropTypes.func.isRequired
};

class Segment {
  constructor(label, x, y, w, h) {
    this.label = label;
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;

    this.isHovered = false;
    this.path = new Path2D();
    this.path.rect(x, y, w, h);
  }

  setIsHovered(isHovered) {
    this.isHovered = isHovered;

    return isHovered;
  }

  equal(other) {
    if (other === null) {
      return false;
    }

    return (
      this.x === other.x &&
      this.y === other.y &&
      this.w === other.w &&
      this.h === other.h &&
      this.label === other.label
    );
  }

  render(ctx) {
    ctx.fillStyle = this.isHovered ? 'orange' : 'rgba(0, 0, 200, 0)';
    ctx.lineWidth = 1;
    ctx.strokeStyle = this.isHovered ? 'orange' : 'black';
    ctx.fill(this.path);
    ctx.stroke(this.path);
  }
}

class ComparisonLine {
  constructor(querySegment, referenceSegment) {
    this.querySegment = querySegment;
    this.referenceSegment = referenceSegment;

    this.path = new Path2D();

    // Assume that query segments are above reference segments and
    // construct a line from the bottom of the query segment to the top
    // of the reference segment
    this.path.moveTo(
      querySegment.x + querySegment.w / 2,
      querySegment.y + querySegment.h
    );
    this.path.lineTo(
      referenceSegment.x + referenceSegment.w / 2,
      referenceSegment.y
    );
  }

  render(ctx) {
    const eitherSegmentIsHovered =
      this.querySegment.isHovered || this.referenceSegment.isHovered;
    ctx.strokeStyle = eitherSegmentIsHovered ? 'orange' : 'black';
    ctx.lineWidth = eitherSegmentIsHovered ? 3 : 1;

    ctx.stroke(this.path);
  }
}
