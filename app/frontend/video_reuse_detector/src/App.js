import React from 'react';
import ReactDropzone from 'react-dropzone'
import axios from 'axios';

import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.min.css';

import 'bootstrap/dist/css/bootstrap.min.css';

const App = () => {
  const onDrop = (files) => {
    // Push all the axios request promise into a single array
    files.map(async file => {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await axios({
          method: 'post',
          url: 'http://localhost:5000/upload',
          data: formData,
          config: { headers: { 'Content-Type': 'multipart/form-data' } }
        });

        console.log(response);
        toast.success(`${file.name} uploaded!`);
      }
      catch (errors) {
        console.log(errors);
        toast.error(`${file.name}, upload failed...`);
      }
    });
  }

    return (
      <div className="app text-center">
        <ReactDropzone 
          onDrop={onDrop}
          multiple
          >
          {({getRootProps, getInputProps, isDragActive}) => (
            <div {...getRootProps()}>
              <input {...getInputProps()} />
              {isDragActive ? "Drop the file to upload it!" : 'Click me or drag a file to upload!'}
            </div>
          )}
        </ReactDropzone>
        <ToastContainer />
      </div>
    );
}

export default App;
