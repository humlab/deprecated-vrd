import React from 'react';
const topY = 100;
const bottomY = 500;
const recWidth = 40;
const recHeight = 25;
const timelines = [];

class Visualisation extends React.Component {
  componentDidMount() {
    const canvas = this.refs.canvas;
    const c = canvas.getContext('2d');
  }

  componentDidUpdate(c, canvas) {
    console.log('update');
    const data = this.props.props;
    console.log(data);
    //Videos att jämföra
    const queryVideoName = 'ATW-645_border.mpg';
    const referenceVideoName = 'ATW-500.mpg';
    // const referenceVideoName = 'Megamind_bugy.avi';
    //Videons längd
    const queryLength = videoLength(queryVideoName, data);
    const referenceLength = videoLength(referenceVideoName, data);
    //Ritar ut rektanglar och retunerar en array med dessa för respektive video.
    const topRow = visualizeSegmentsAndTimelines(queryLength, topY); //Videons längd, x-värde och namn
    const bottomRow = visualizeSegmentsAndTimelines(referenceLength, bottomY);

    const lines = simScoreLines(
      topRow,
      bottomRow,
      data,
      c,
      queryVideoName,
      referenceVideoName,
    );

    const rectangles = [...topRow, ...bottomRow];
    const all = [...rectangles, ...lines, ...timelines];

    //   window.addEventListener('mousemove', function(e) {
    //     const rec = this.getBoundingClientRect();
    //     const x = e.clientX - rec.left;
    //     const y = e.clientY - rec.top;

    //     topRow.map(r => r.setIsHovered(c.isPointInPath(r.path, x, y)));
    //     bottomRow.map(r => r.setIsHovered(c.isPointInPath(r.path, x, y)));
    //   });

    //   function onHover() {
    //     //c.clearRect(0, 0, canvas.width, canvas.height);
    //     //videoNamesRender(queryVideoName, referenceVideoName);
    //     //all.map(r => r.render(c));

    //     requestAnimationFrame(onHover);
    //   }
    //   onHover();
  }

  render() {
    return (
      <div>
        <canvas ref="canvas" width={500} height={500}></canvas>
      </div>
    );
  }
}
export default Visualisation;

//Räknar ut en videos längd och retunerar dess maxvärde.
function videoLength(videoName, data) {
  const queryName = data.filter(obj => obj.query_video_name === videoName); //Hämtar alla objekt för videonamn som passar
  const referenceName = data.filter(obj => obj.reference_video_name === videoName); //Hämtar alla objekt för videonamn som passar
  const query_segment_ids = queryName.map(o => o.query_segment_id); //Alla query Ids om det finns.
  const max_query_segment_id = [...new Set(query_segment_ids)].length; //Längd av query video, 0 om det inte är en queryvideo.
  const reference_segment_ids = referenceName.map(o => o.reference_segment_id); //Alla reference Ids om det finns.
  const max_reference_segment_id = [...new Set(reference_segment_ids)].length; // Längd av reference video, 0 om det inte är en referencevideo.

  return Math.max(max_query_segment_id, max_reference_segment_id); //Retunerar längden av den video som innehåller något.
}

//Klass för att rendera rektanglar för videosegment.
class Rectangle {
  constructor(x, y, w, h) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;

    this.isHovered = false;
    this.path = new Path2D();
    this.path.rect(x, y, w, h);
    this.lines = [];
  }

  addLines(line) {
    this.lines.push(line);
  }

  setIsHovered(ToF) {
    this.isHovered = ToF;
    this.lines.forEach(l => {
      if (!l.recIsActive) {
        l.recIsActive = ToF;
      }
    });
  }

  render(c) {
    c.fillStyle = this.isHovered ? 'orange' : 'rgba(0, 0, 200, 0)';
    c.lineWidth = 1;
    c.strokeStyle = this.isHovered ? 'orange' : 'black';
    c.fill(this.path);
    c.stroke(this.path);
    c.fillStyle = 'black';
  }
}

//Klass för att rendera tidsstreck för varje 5 segment.
class Timeline {
  constructor(x, y, sek) {
    this.x = x;
    this.y = y;
    this.sek = sek;
  }

  render(c) {
    c.beginPath();
    c.lineWidth = 1;
    c.setLineDash([4, 3]);
    c.strokeStyle = 'black';
    c.save();
    c.moveTo(this.x, this.y);

    if (this.y === topY) {
      c.lineTo(this.x, this.y - recHeight);
      c.translate(this.x, this.y - recHeight - 10);
      c.rotate(-Math.PI / 2);
    } else if (this.y === bottomY) {
      c.lineTo(this.x, this.y + recHeight * 2);
      c.translate(this.x, this.y + recHeight * 3 + 10);
      c.rotate(-Math.PI / 2);
    }

    c.fillText(this.sek + ' sek', 0, 0);
    c.stroke();
    c.restore();
    c.setLineDash([0, 0]);
  }
}

//Klass för att rendera linjer för likhet.
class Line {
  constructor(top, bottom, simScore) {
    this.recIsActive = false;
    this.top = top;
    this.bottom = bottom;
    this.simScore = simScore;

    this.top.addLines(this);
    this.bottom.addLines(this);

    this.path = new Path2D();
    this.path.moveTo(top.x + recWidth / 2, top.y + recHeight);
    this.path.lineTo(bottom.x + recWidth / 2, bottom.y);
  }

  render(c) {
    c.strokeStyle = this.recIsActive ? 'orange' : this.style(c);
    c.lineWidth = this.recIsActive ? 3 : this.style(c);
    // const proc = this.simScore * 100;

    if (this.recIsActive && (this.top.isHovered || this.bottom.isHovered)) {
      c.font = 'bold 14px Arial';
      c.fillStyle = this.style(c);
      c.strokeStyle = 'orange';
      c.lineWidth = 4;

      if (this.top.isHovered) {
        c.fillText(
          this.simScore.toFixed(3),
          this.bottom.x + 3,
          this.bottom.y + this.bottom.h / 1.5,
        );
      } else if (this.bottom.isHovered) {
        c.fillText(this.simScore.toFixed(3), this.top.x + 3, this.top.y + this.top.h / 1.5);
      }
    } else {
      c.strokeStyle = this.style(c);
      c.lineWidth = this.style(c);
    }
    c.stroke(this.path);
    c.font = '12px Arial';
    c.fillStyle = 'black';
  }

  style(c) {
    const colors = ['#636363', '#007bff', '#0e0c8a'];

    if (this.simScore >= 0.3 && this.simScore < 0.6) {
      c.lineWidth = 0.5;
      c.strokeStyle = colors[0];
      c.fillStyle = colors[0];
    } else if (this.simScore >= 0.6 && this.simScore < 0.9) {
      c.lineWidth = 1;
      c.strokeStyle = colors[1];
      c.fillStyle = colors[1];
    } else if (this.simScore >= 0.9) {
      c.lineWidth = 2;
      c.strokeStyle = colors[2];
      c.fillStyle = colors[2];
    }
  }
}

function visualizeSegmentsAndTimelines(videoLength, y) {
  let x = 50;
  let sek = 0;
  const rectangles = [];

  for (let i = 0; i < videoLength; i++) {
    let r = new Rectangle(x, y, recWidth, recHeight);
    rectangles.push(r);

    if (i % 5 === 0 && i !== 0) {
      if (y === bottomY) {
        let t = new Timeline(x, y, sek);
        timelines.push(t);
      } else {
        let t = new Timeline(x, y, sek);
        timelines.push(t);
      }
    }
    x = x + recWidth;
    sek++;
  }

  return rectangles;
}

function simScoreLines(topRow, bottomRow, data, c, queryVideoName, referenceVideoName) {
  const items = data.filter(
    o =>
      o.query_video_name === queryVideoName && o.reference_video_name === referenceVideoName,
  );
  const lines = [];

  items.forEach(item => {
    let qID = item.query_segment_id;
    let rID = item.reference_segment_id;
    let simScore = item.similarity_score;

    if (simScore >= 0.3 && simScore < 0.6) {
      let line = new Line(topRow[qID], bottomRow[rID], simScore);
      lines.push(line);
    } else if (simScore >= 0.6 && simScore < 0.9) {
      let line = new Line(topRow[qID], bottomRow[rID], simScore);
      lines.push(line);
    } else if (simScore >= 0.9) {
      let line = new Line(topRow[qID], bottomRow[rID], simScore);
      lines.push(line);
    }
  });

  lines.map(line => line.style(c));

  return lines;
}

function videoNamesRender(queryVideoName, referenceVideoName, c) {
  c.font = 'bold 18px Arial';
  c.fillStyle = 'black';
  c.fillText(queryVideoName, 50, topY - recHeight * 2);
  c.fillText(referenceVideoName, 50, bottomY + recHeight * 3);
  c.font = '12px Arial';
}
