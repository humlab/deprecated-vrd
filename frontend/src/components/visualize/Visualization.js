import React from 'react';
import PropTypes from 'prop-types';

import Paper from '@material-ui/core/Paper';
import { Link } from 'react-router-dom';

// https://stackoverflow.com/a/34796988/5045375
function round(value, decimals) {
  return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals).toFixed(
    decimals
  );
}

const matchLevels = [
  // G is never rendered, why? Because it means there is no similarity.
  'MatchLevel.LEVEL_A',
  'MatchLevel.LEVEL_B',
  'MatchLevel.LEVEL_C',
  'MatchLevel.LEVEL_D',
  'MatchLevel.LEVEL_E',
  'MatchLevel.LEVEL_F'
];

// https://stackoverflow.com/a/5624139/5045375
function hexToRGB(hexadecimalColor) {
  // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
  const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
  const hex = hexadecimalColor.replace(shorthandRegex, function(_, r, g, b) {
    return r + r + g + g + b + b;
  });

  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      }
    : null;
}

const matchLevelToSwatchMap = {
  [matchLevels[0]]: '#ef5080', // Rich midtone magenta
  [matchLevels[1]]: '#745af7', // rich midtone blue
  [matchLevels[2]]: '#62f9d0', // rich midtone green
  [matchLevels[3]]: '#5cac77', // pale midtone green
  [matchLevels[4]]: '#f3f3a0', // rich light yellow
  [matchLevels[5]]: '#e1e5d9' // Worst, neutral light-green
};

const matchLevelToAlphaMap = {
  [matchLevels[0]]: 1.0, // Best match
  [matchLevels[1]]: 0.5, // th, cc, not ORB ssm OK
  [matchLevels[2]]: 0.3, // th, cc, not ORB, SSM unavailable
  [matchLevels[3]]: 0.6, // Pretty good visual match  (th, ORB). No color available
  [matchLevels[4]]: 0.2, // th & ssm
  [matchLevels[5]]: 0.1 // worst of the lot
};

function hexToRGBA(hexidecimalColor, alpha) {
  const { r, g, b } = hexToRGB(hexidecimalColor);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function matchLevelToRGBA(matchLevel) {
  return hexToRGBA(
    matchLevelToSwatchMap[matchLevel],
    matchLevelToAlphaMap[matchLevel]
  );
}

const matchLevelToDescription = {
  'MatchLevel.LEVEL_A': 'Visual fingerprints matched. Did not compare audio',

  // Note: LEVEL_B currently never happens as we never consider audio
  'MatchLevel.LEVEL_B':
    'ORB fingerprint does not have any matched keypoint but the other three fingerprints (th, cc, ssm) do, then we consider that video as a possible matching. This case assumes that the ORB fingerprint was affected by the visual transformations.',
  'MatchLevel.LEVEL_C':
    'The first two filtering levels (Th and CC)  have  good  similarity although ORB did not resist the transformations and there is no audio information.',
  'MatchLevel.LEVEL_D':
    'The video is in grayscale and was matched local keypoints',

  // Note: LEVEL_E currently never happens
  'MatchLevel.LEVEL_E':
    'The video is in grayscale, ORB did not resist but the audio fingerprint matched',

  'MatchLevel.LEVEL_F': 'The video is in grayscale, only thumbnails matched'
};

export default class Visualization extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      selected: false
      // label: '',
      // x: -1,
      // y: -1,
      // w: -1,
      // h: -1
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

  createQueryVideoFileLink(videoName) {
    return (
      <Link to={`/api/files/uploads/${videoName}`} target="_blank">
        {videoName}
      </Link>
    );
  }

  createReferenceVideoFileLink(videoName) {
    return (
      <Link to={`/api/files/archive/${videoName}`} target="_blank">
        {videoName}
      </Link>
    );
  }

  createMatchLevelDistribution(comparison) {
    const comparisonsByMatchLevel = comparison.comparisons;

    const matchLevelToNumberOfMatches = {};
    const rectangles = [];
    let xOffset = 0;
    const totalWidth = 100;

    for (let [matchLevel, matches] of Object.entries(comparisonsByMatchLevel)) {
      matchLevelToNumberOfMatches[matchLevel] = matches.length;
      const width = (totalWidth * matches.length) / comparison.totalMatches;
      const fillStyle = matchLevelToSwatchMap[matchLevel];

      rectangles.push(
        <rect x={xOffset} width={width} height="50" fill={fillStyle}>
          <title>{matchLevelToDescription[matchLevel]}</title>
        </rect>
      );

      xOffset += width;
    }

    const totalMatches = Object.values(matchLevelToNumberOfMatches).reduce(
      (a, b) => a + b
    );
    if (totalMatches !== comparison.totalMatches) {
      console.log(
        `Expected to gather up all matches, but did not. Actual=${totalMatches} expected=${comparison.totalMatches}`
      );
    }

    return rectangles;
  }

  createHeader(comparison) {
    const queryVideoLink = this.createQueryVideoFileLink(
      comparison.queryVideoName
    );
    const referenceVideoLink = this.createReferenceVideoFileLink(
      comparison.referenceVideoName
    );

    const possibleDistinctMatches =
      comparison.numberOfQuerySegments + comparison.numberOfReferenceSegments;
    const distinctMatches = comparison.distinctMatches;
    const rating = (100 * distinctMatches) / possibleDistinctMatches;
    const rectangles = this.createMatchLevelDistribution(comparison);

    return (
      <h3>
        {queryVideoLink} / {referenceVideoLink} ({round(rating, 1)}%){' '}
        <svg width="125" height="25">
          {rectangles}
        </svg>
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
  moveLeftButton = null;
  moveRightButton = null;

  queryVideoName = null;
  referenceVideoName = null;

  querySegments = [];
  referenceSegments = [];
  queryTimelines = [];
  referenceTimelines = [];

  segments = [...this.querySegments, ...this.referenceSegments];

  lines = [];
  timelines = [];

  componentDidMount() {
    console.log('Mount')
    this.ctx = this.canvas.getContext('2d');
    this.ctx.strokeStyle = this.props.strokeStyle;
    this.ctx.lineWidth = this.props.lineWidth;
    this.addMouseEvents();
  }

  componentDidUpdate() {
    const comparison = this.props.comparison;

    if (comparison.length === 0) {
      console.log('WARN: No comparison to render, this should never happen!');
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
    this.querySegments = createSegments('Query Segment', queryLength, 100);
    this.queryTimelines = createTimelines(this.querySegments);

    console.log(
      `Creating ${referenceLength} segments for reference video ${this.referenceVideoName}`
    );
    this.referenceSegments = createSegments(
      'Reference Segment',
      referenceLength,
      500
    );
    this.referenceTimelines = createTimelines(this.referenceSegments);

    this.segments = [...this.querySegments, ...this.referenceSegments];

    this.lines = createComparisonLines(
      this.querySegments,
      this.referenceSegments,
      comparison.comparisons
    );

    this.moveLeftButton = new MoveButton(50, 600, 100, 30);
    this.moveRightButton = new MoveButton(160, 600, 100, 30);

    this.shouldRender = true;
    requestAnimationFrame(this.updateCanvas);
  }

  componentWillUnmount() {
    this.removeMouseEvents();
  }

  updateCanvas = () => {
    if (!this.shouldRender) {
      return;
    }

    // console.log('Clearing canvas and rendering items');
    this.ctx.clearRect(0, 0, this.props.width, this.props.height);
    this.segments.map(o => o.render(this.ctx));
    this.lines.map(o => o.render(this.ctx));
    this.moveLeftButton.render(this.ctx);
    this.moveRightButton.render(this.ctx);
    this.queryTimelines.map(o => o.render(this.ctx));
    this.referenceTimelines.map(o => o.render(this.ctx));

    this.shouldRender = false;
  };

  addMouseEvents() {
    this.canvas.addEventListener('mousemove', this.onMouseMove, false);
    this.canvas.addEventListener('mousedown', this.onMouseDown, false);
    this.canvas.addEventListener('mouseup', this.onMouseUp, false);
  }

  removeMouseEvents() {
    this.canvas.removeEventListener('mousemove', this.onMouseMove, false);
    this.canvas.removeEventListener('mouseup', this.onMouseUp, false);
    this.canvas.removeEventListener('mousedown', this.onMouseDown, false);
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
          // console.log(
          //   `Was not hovering over anything, now hovering over ${segment.label}`
          // );

          this.shouldRender = true;
          this.objectUnderMouse = segment;

          isHovering = true;
        } else if (!segment.equal(this.objectUnderMouse)) {
          // the mouse is over a different object than before,
          // console.log(
          //   `Was hovering over ${this.objectUnderMouse.label}. Now hovering over ${segment.label}`
          // );
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
      // console.log(
      //   `Was hovering over ${this.objectUnderMouse.label}. Now hovering over nothing`
      // );
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

  onMouseUp = e => {
    this.moveLeftButton.setIsClicked(false);
    this.moveRightButton.setIsClicked(false);
    this.shouldRender = true;
    requestAnimationFrame(this.updateCanvas);
  };

  onMouseDown = e => {
    // console.log(this.referenceSegments[0].x);
    const rec = this.canvas.getBoundingClientRect();
    const curX = e.clientX - rec.left;
    const curY = e.clientY - rec.top;
    this.moveLeftButton.setIsClicked(
      this.ctx.isPointInPath(this.moveLeftButton.path, curX, curY)
    );
    this.moveRightButton.setIsClicked(
      this.ctx.isPointInPath(this.moveRightButton.path, curX, curY)
    );

    if (this.moveLeftButton.isClicked) {
      this.referenceSegments.map(o => (o.x -= 1));
    } else if (this.moveRightButton.isClicked) {
      this.referenceSegments.map(o => (o.x += 1));
    }

    this.shouldRender = true;
    requestAnimationFrame(this.updateCanvas);
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

class MoveButton {
  constructor(x, y, w, h) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;

    this.isClicked = false;
    this.path = new Path2D();
    this.path.rect(x, y, w, h);
  }

  setIsClicked(isClicked) {
    this.isClicked = isClicked;
    return isClicked;
  }

  render(ctx) {
    ctx.save();
    ctx.fillStyle = this.isClicked ? '#e8e8e8' : 'orange';
    ctx.fill(this.path);

    ctx.beginPath();
    ctx.strokeStyle = this.isClicked ? 'orange' : 'black';
    ctx.fillStyle = this.isClicked ? 'orange' : 'black';
    ctx.lineWidth = 1;
    //prettier way to do this?
    if (this.x === 50) {
      ctx.moveTo(this.x + (this.w / 4) * 3, this.y + this.h / 2);
      ctx.lineTo(this.x + this.w / 4, this.y + this.h / 2);
      ctx.lineTo(this.x + (this.w / 6) * 2, this.y + this.h / 4);
      ctx.lineTo(this.x + (this.w / 6) * 2, this.y + (this.h / 4) * 3);
      ctx.lineTo(this.x + this.w / 4, this.y + this.h / 2);
    } else if (this.x === 160) {
      ctx.moveTo(this.x + this.w / 4, this.y + this.h / 2);
      ctx.lineTo(this.x + (this.w / 4) * 3, this.y + this.h / 2);
      ctx.lineTo(this.x + (this.w / 6) * 4, this.y + this.h / 4);
      ctx.lineTo(this.x + (this.w / 6) * 4, this.y + (this.h / 4) * 3);
      ctx.lineTo(this.x + (this.w / 4) * 3, this.y + this.h / 2);
    }
    ctx.stroke();
    ctx.fill();
    ctx.restore();
  }
}

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
  constructor(querySegment, referenceSegment, similarityScore, matchLevel) {
    this.querySegment = querySegment;
    this.referenceSegment = referenceSegment;
    this.similarityScore = similarityScore;
    this.matchLevel = matchLevel;

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

    if (eitherSegmentIsHovered) {
      const orange = '#FFA500';
      ctx.strokeStyle = hexToRGBA(
        orange,
        matchLevelToAlphaMap[this.matchLevel]
      );
      ctx.lineWidth = 3;
    } else {
      console.log(this.matchLevel);
      ctx.strokeStyle = matchLevelToRGBA(this.matchLevel);
      ctx.lineWidth = 1;
    }

    ctx.font = 'bold 14px Arial';

    if (this.querySegment.isHovered) {
      ctx.fillText(
        this.similarityScore.toFixed(3),
        this.referenceSegment.x + 3,
        this.referenceSegment.y + this.referenceSegment.h / 1.5
      );
    } else if (this.referenceSegment.isHovered) {
      ctx.fillText(
        this.similarityScore.toFixed(3),
        this.querySegment.x + 3,
        this.querySegment.y + this.querySegment.h / 1.5
      );
    }

    ctx.font = '12px Arial';

    ctx.stroke(this.path);
  }
}

class Timeline {
  constructor(x, y, sec, recWidth, recHeight) {
    this.x = x;
    this.y = y;
    this.sec = sec;
    this.recWidth = recWidth;
    this.recHeight = recHeight;
  }

  render(ctx) {
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 3]);
    ctx.strokeStyle = 'black';
    ctx.fillStyle = 'black';
    ctx.save();
    ctx.moveTo(this.x, this.y);

    if (this.y === 100) {
      ctx.lineTo(this.x, this.y - this.recHeight);
      ctx.translate(this.x, this.y - this.recHeight - 10);
      ctx.rotate(-Math.PI / 2);
    } else if (this.y === 500) {
      ctx.lineTo(this.x, this.y + this.recHeight * 2);
      ctx.translate(this.x, this.y + this.recHeight * 3 + 10);
      ctx.rotate(-Math.PI / 2);
    }

    ctx.fillText(this.sec + ' sec', 0, 0);
    ctx.stroke();
    ctx.restore();
    ctx.setLineDash([0, 0]);
  }
}

function createSegments(
  labelSeed,
  nrOfSegments,
  yOffset,
  recWidth = 44,
  recHeight = 44,
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

function createComparisonLines(
  querySegments,
  referenceSegments,
  comparisons
) {
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
        similarityScore,
        comparison.match_level
      );
      lines.push(line);
    }
  });

  return lines;
}

function createTimelines(segments) {
  const timelines = [];
  let sec = 0;

  for (const [i, segment] of segments.entries()) {
    if (i % 5 === 0 && i !== 0) {
      let t = new Timeline(segment.x, segment.y, sec, segment.w, segment.h);
      timelines.push(t);
    }
    sec++;
  }
  return timelines;
}
