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
        <Canvas
          width={3000}
          height={780}
          onSelected={this.onSelected}
          comparison={this.props.comparison}
        />
        <div>{this.getSelectionStr()}</div>
      </div>
    );
  }
}

Visualization.propTypes = {
  comparison: PropTypes.array.isRequired
};

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

  queryVideoName = null;
  referenceVideoName = null;

  querySegments = [];
  referenceSegments = [];

  segments = [...this.querySegments, ...this.referenceSegments];

  lines = [];

  curX = -1;
  curY = -1;

  componentDidMount() {
    this.ctx = this.canvas.getContext('2d');
    this.ctx.strokeStyle = this.props.strokeStyle;
    this.ctx.lineWidth = this.props.lineWidth;
    this.addMouseEvents();
  }

  componentDidUpdate() {
    const comparison = this.props.comparison;
    if (comparison.length == 0) {
      console.log('No comparison to render');
      return;
    }

    const queryVideoName = 'ATW-644_hflip.mpg';
    const referenceVideoName = 'ATW-644.mpg';

    if (
      this.queryVideoName === queryVideoName ||
      this.referenceVideoName === referenceVideoName
    ) {
      console.log('Component update: but video did not change');
      return;
    }

    console.log(
      'Comparing other videos than before. Recreating objects that make up visualization'
    );

    this.queryVideoName = queryVideoName;
    this.referenceVideoName = referenceVideoName;

    const queryLength = videoLength(queryVideoName, comparison);
    const referenceLength = videoLength(referenceVideoName, comparison);

    this.querySegments = createSegments('Query Segment', queryLength, 50);

    this.referenceSegments = createSegments(
      'Reference Segment',
      referenceLength,
      500
    );

    this.segments = [...this.querySegments, ...this.referenceSegments];

    this.lines = createComparisonLines(
      this.querySegments,
      this.referenceSegments,
      comparison,
      queryVideoName,
      referenceVideoName
    );

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
  onSelected: PropTypes.func.isRequired,
  comparison: PropTypes.array.isRequired
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

function createSegments(
  labelSeed,
  nrOfSegments,
  yOffset,
  recWidth = 40,
  recHeight = 25,
  xOffset = 50
) {
  let currentX = xOffset;
  const segments = [];

  for (let i = 0; i < nrOfSegments; i++) {
    const segment = new Segment(
      `${labelSeed} ${i}`,
      currentX,
      yOffset,
      recWidth,
      recHeight
    );
    segments.push(segment);

    currentX += recWidth;
  }

  return segments;
}

function videoLength(videoName, comparison) {
  const queryObjects = comparison.filter(
    obj => obj.query_video_name === videoName
  );
  const referenceObjects = comparison.filter(
    obj => obj.reference_video_name === videoName
  );
  const querySegmentIds = queryObjects.map(o => o.query_segment_id);
  const maxQuerySegmentId = [...new Set(querySegmentIds)].length;
  const referenceSegmentIds = referenceObjects.map(o => o.reference_segment_id);
  const maxReferenceSegmentId = [...new Set(referenceSegmentIds)].length;

  return Math.max(maxQuerySegmentId, maxReferenceSegmentId);
}

function createComparisonLines(
  querySegments,
  referenceSegments,
  comparison,
  queryVideoName,
  referenceVideoName
) {
  const items = comparison.filter(
    o =>
      o.query_video_name === queryVideoName &&
      o.reference_video_name === referenceVideoName
  );
  const lines = [];

  items.forEach(item => {
    const qID = item.query_segment_id;
    const rID = item.reference_segment_id;
    const similarityScore = item.similarity_score;

    if (similarityScore >= 0.3) {
      let line = new ComparisonLine(
        querySegments[qID],
        referenceSegments[rID],
        similarityScore
      );
      lines.push(line);
    }
  });

  return lines;
}
