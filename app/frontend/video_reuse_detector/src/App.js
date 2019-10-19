import React from "react";
import Dropzone from "react-dropzone-uploader";

import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.min.css";

import "bootstrap/dist/css/bootstrap.min.css";
import "react-dropzone-uploader/dist/styles.css";

const App = () => {
  const getUploadParams = () => {
    return { url: "http://localhost:5000/upload" };
  };

  const handleChangeStatus = ({ meta, remove }, status) => {
    if (status === "headers_received") {
      toast.success(`${meta.name} uploaded!`);
      remove();
    } else if (status === "aborted") {
      toast.error(`${meta.name}, upload failed...`);
    }
  };

  return (
    <div className="app text-center">
      <Dropzone
        getUploadParams={getUploadParams}
        onChangeStatus={handleChangeStatus}
        styles={{
          dropzone: { width: 400, height: 200 },
          dropzoneActive: { borderColor: "green" }
        }}
      />
      <ToastContainer />
    </div>
  );
};

export default App;
