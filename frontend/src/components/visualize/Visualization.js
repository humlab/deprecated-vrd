import React from 'react';
import PropTypes from 'prop-types';

import Paper from '@material-ui/core/Paper';

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

  createHeader(comparison) {
    return (
      <h3>
        {comparison.queryVideoName} / {comparison.referenceVideoName}
      </h3>
    );
  }

  render() {
    return (
      <Paper style={{ padding: '1.5em', margin: '0.5em' }}>
        {this.createHeader(this.props.comparison)}
        <Canvas
          width={3000}
          height={780}
          onSelected={this.onSelected}
          comparison={this.props.comparison}
        />
        <div>{this.getSelectionStr()}</div>
      </Paper>
    );
  }
}

Visualization.propTypes = {
  comparison: PropTypes.object.isRequired
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

  componentDidMount() {
    this.ctx = this.canvas.getContext('2d');
    this.ctx.strokeStyle = this.props.strokeStyle;
    this.ctx.lineWidth = this.props.lineWidth;
    this.addMouseEvents();
  }

  componentDidUpdate() {
    const comparison = this.props.comparison;
    if (comparison.length === 0) {
      console.log('No comparison to render');
      return;
    }

    const queryVideoName = comparison.queryVideoName;
    const referenceVideoName = comparison.referenceVideoName;

    if (
      this.queryVideoName === queryVideoName ||
      this.referenceVideoName === referenceVideoName
    ) {
      console.log(
        `Component update: comparing same videos as before.
        Query Video=${this.queryVideoName}.
        Reference Video=${this.referenceVideoName}.
        Doing nothing!`
      );
      return;
    }

    console.log(
      `Component update comparing other videos than before.
      Previous Query Video: ${this.queryVideoName},
      Previous Reference Video: ${this.referenceVideoName}
      New Query Video: ${queryVideoName}
      Reference Video ${referenceVideoName}.
      Recreating objects that make up visualization`
    );

    this.queryVideoName = queryVideoName;
    this.referenceVideoName = referenceVideoName;

    const queryLength = comparison.numberOfQuerySegments;
    const referenceLength = comparison.numberOfReferenceSegments;

    console.log(
      `Creating ${queryLength} segments for query video ${this.queryVideoName}`
    );
    this.querySegments = createSegments('Query Segment', queryLength, 50);

    console.log(
      `Creating ${referenceLength} segments for reference video ${this.referenceVideoName}`
    );
    this.referenceSegments = createSegments(
      'Reference Segment',
      referenceLength,
      500
    );

    this.segments = [...this.querySegments, ...this.referenceSegments];

    this.lines = createComparisonLines(
      this.querySegments,
      this.referenceSegments,
      comparison.comparisons
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

    this.shouldRender = false;
  };

  componentWillUnmount() {
    this.removeMouseEvents();
  }

  addMouseEvents() {
    this.canvas.addEventListener('mousemove', this.onMouseMove, false);
  }

  removeMouseEvents() {
    this.canvas.removeEventListener('mousemove', this.onMouseMove, false);
  }

  onMouseMove = e => {
    const curX = e.offsetX;
    const curY = e.offsetY;

    const wasHovering = this.objectUnderMouse !== null;
    let isHovering = false;

    for (const segment of this.segments) {
      const mouseIsOverObject = segment.setIsHovered(
        this.ctx.isPointInPath(segment.path, curX, curY)
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
  comparison: PropTypes.object.isRequired
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
  constructor(querySegment, referenceSegment, similarityScore) {
    this.querySegment = querySegment;
    this.referenceSegment = referenceSegment;
    this.similarityScore = similarityScore;

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
    const colors = ['#636363', '#007bff', '#0e0c8a'];

    const eitherSegmentIsHovered =
      this.querySegment.isHovered || this.referenceSegment.isHovered;

    if (eitherSegmentIsHovered) {
      ctx.strokeStyle = 'orange';
      ctx.lineWidth = 3;
    } else if (this.similarityScore >= 0.3 && this.similarityScore < 0.6) {
      ctx.lineWidth = 0.5;
      ctx.strokeStyle = colors[0];
      ctx.fillStyle = colors[0];
    } else if (this.similarityScore >= 0.6 && this.similarityScore < 0.9) {
      ctx.lineWidth = 1;
      ctx.strokeStyle = colors[1];
      ctx.fillStyle = colors[1];
    } else if (this.similarityScore >= 0.9) {
      ctx.lineWidth = 2;
      ctx.strokeStyle = colors[2];
      ctx.fillStyle = colors[2];
    } else {
      // These lines should not have been created. Make sure they stand out!
      ctx.strokeStyle = 'green';
      ctx.lineWidth = 10;
    }

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

function createComparisonLines(querySegments, referenceSegments, comparisons) {
  const lines = [];

  // Comparisons are a bunch of comparison objects grouped by match level, i.e.
  //
  // {
  //   'MatchLevel.LEVEL_A': [...]
  //   'MatchLevel.LEVEL_B': [...]
  // }
  //
  // and we can join the list together thusly,
  const flattenedComparisons = Array.prototype.concat(
    ...Object.values(comparisons)
  );

  flattenedComparisons.forEach(comparison => {
    const qID = comparison.query_segment_id;
    const rID = comparison.reference_segment_id;
    const similarityScore = comparison.similarity_score;

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
