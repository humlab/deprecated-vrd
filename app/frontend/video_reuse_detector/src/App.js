import React from "react";
import Dropzone from "react-dropzone-uploader";
import axios from "axios";

import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.min.css";

import openSocket from "socket.io-client";

import "bootstrap/dist/css/bootstrap.min.css";
import "react-dropzone-uploader/dist/styles.css";

const FileTable = props => {
  const { files } = props;
  return (
    <div className="files">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">State</th>
          </tr>
        </thead>
        <tbody>
          {files.map(f => (
            <FileListing key={f.filename} file={f} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

const FileListing = props => {
  const { filename, state } = props.file;

  return (
    <tr>
      <th scope="row">{filename}</th>
      <td>{state}</td>
    </tr>
  );
};

const socket = openSocket("http://localhost:5000/");

class App extends React.Component {
  state = {
    files: []
  };

  componentDidMount() {
    this.listFiles();
    socket.on("state_change", this.listFiles);
  }

  componentWillUnmount() {
    socket.off("state_change");
  }

  listFiles = async () => {
    axios.get("http://localhost:5000/list").then(res => {
      this.setState({ files: res.data });
    });
  };

  getUploadParams = () => {
    return { url: "http://localhost:5000/upload" };
  };

  handleChangeStatus = ({ meta, remove }, status) => {
    if (status === "headers_received") {
      toast.success(`${meta.name} uploaded!`);
      this.listFiles();
      remove();
    } else if (status === "aborted") {
      toast.error(`${meta.name}, upload failed...`);
    }
  };

  render() {
    return (
      <div className="app container">
        <div className="row">
          <div className="col">
            <Dropzone
              getUploadParams={this.getUploadParams}
              onChangeStatus={this.handleChangeStatus}
              styles={{
                dropzoneActive: { borderColor: "green" }
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

export default App;
