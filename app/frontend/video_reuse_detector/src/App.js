import React, { Component } from 'react';
import ReactDropzone from 'react-dropzone'
import axios from 'axios';

import 'bootstrap/dist/css/bootstrap.min.css';

class App extends Component {

  onDrop = (files) => {
    const formData = new FormData();

    formData.append("file", files[0]);

    axios({
      method: 'post',
      url: 'http://localhost:5000/upload',
      data: formData,
      config: { headers: { 'Content-Type': 'multipart/form-data' } }
    })
    .then(response => console.log(response))
    .catch(errors => console.log(errors))

  }

  render() {
    return (
      <div className="app text-center">
        <ReactDropzone 
          onDrop={this.onDrop}
          multiple
          >
          {({getRootProps, getInputProps, isDragActive}) => (
            <div {...getRootProps()}>
              <input {...getInputProps()} />
              {isDragActive ? "Drop the file to upload it!" : 'Click me or drag a file to upload!'}
            </div>
          )}
        </ReactDropzone>
      </div>
    );
  }
}

export default App;
