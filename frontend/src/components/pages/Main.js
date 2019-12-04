import React, { Component } from 'react';

import Dropzone from 'react-dropzone-uploader';
import { ToastContainer, toast } from 'react-toastify';

import axios from 'axios';
import openSocket from 'socket.io-client';

import FileTable from '../files/FileTable';

const socket = openSocket(`${process.env.REACT_APP_API_URL}`);

export default class Main extends Component {
  state = {
    files: {}
  };

  componentDidMount() {
    this.listFiles();
    socket.on('state_change', this.updateFileState);
  }

  componentWillUnmount() {
    socket.off('state_change');
  }

  listFiles = async () => {
    // Fetch the file list, which is a bunch of
    // key-value pairs on the form,
    //
    // {"files": [{"processing_state": "FINGERPRINTED", "video_name": "Megamind.avi", ...}, {...}]}
    //
    // and a few other attributes
    const { data } = await axios.get(
      `${process.env.REACT_APP_API_URL}/api/files/list`
    );

    const files = data.files;

    // Make it so that the video_name is the key to the rest of the attributes,
    //
    // {"Megamind.avi": {"processing_state": "FINGERPRINTED", ...}
    const nameToObjList = files.map(obj => ({
      [obj.video_name]: obj
    }));

    const nameToObjDictionary = nameToObjList.reduce((map, x) => {
      Object.keys(x).forEach(key => {
        map[key] = x[key];
      });

      return map;
    }, {});

    // And overlay it with the previous state.
    //
    // The syntax "{ ...o1, ...o2 }" will overwrite the values in
    // o1 with the values in o2 if there are overlapping keys
    this.setState(prevState => ({
      files: {
        ...prevState.files,
        ...nameToObjDictionary
      }
    }));
  };

  updateFileState = response => {
    const { video_name, processing_state, type } = response;

    this.setState(prevState => ({
      files: {
        ...prevState.files,
        [video_name]: { processing_state: processing_state, type: type }
      }
    }));
  };

  getUploadParams = () => {
    return { url: `${process.env.REACT_APP_API_URL}/api/files/upload` };
  };

  handleChangeStatus = ({ meta, remove }, status) => {
    const errorStates = [
      'error_file_size',
      'error_validation',
      'error_upload_params',
      'exception_upload',
      'error_upload'
    ];

    if (status === 'headers_received') {
      toast.success(`${meta.name} uploaded!`);

      // Mark the file as unprocessed
      this.setState(prevState => ({
        files: {
          ...prevState.files,
          [meta.name]: { type: 'UPLOAD', processing_state: 'UPLOADED' }
        }
      }));

      // Remove the toast notification
      remove();
    } else if (status === 'aborted') {
      toast.warn(`${meta.name}, upload aborted...`);
    } else if (errorStates.includes(status)) {
      toast.error(`${meta.name}, upload failed... status=${status}`);
    }
  };
  render() {
    return (
      <div>
        <div className="row">
          <div className="col">
            <Dropzone
              getUploadParams={this.getUploadParams}
              onChangeStatus={this.handleChangeStatus}
              styles={{
                dropzoneActive: { borderColor: 'green' }
              }}
            />
            <ToastContainer />
          </div>
        </div>
        <div className="row mt-5">
          <div className="col">
            <FileTable files={this.state.files} />
          </div>
        </div>
      </div>
    );
  }
}
