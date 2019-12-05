import React, { useEffect, useState } from 'react';

import Dropzone from 'react-dropzone-uploader';
import { ToastContainer, toast } from 'react-toastify';

import axios from 'axios';
import openSocket from 'socket.io-client';

import FileTable from '../files/FileTable';
import Button from '@material-ui/core/Button';

const socket = openSocket(`${process.env.REACT_APP_API_URL}`);

export default function Main() {
  const [allFiles, setAllFiles] = useState({});
  const [selectedUploads, setSelectedUploads] = useState([]);
  const [selectedArchiveFiles, setSelectedArchiveFiles] = useState([]);

  useEffect(() => {
    listFiles();
    socket.on('state_change', updateFileState);

    return () => {
      socket.off('state_change');
    };
  }, []);

  const listFiles = async () => {
    // Fetch the file list, which is a bunch of
    // key-value pairs on the form,
    //
    // {"files": [{"processing_state": "FINGERPRINTED", "video_name": "Megamind.avi", ...}, {...}]}
    //
    // and a few other attributes
    const { data } = await axios.get(
      `${process.env.REACT_APP_API_URL}/api/files/list`
    );

    const files = data.files || [];

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
    setAllFiles(allFiles => ({
      ...allFiles,
      ...nameToObjDictionary
    }));
  };

  const updateFileState = response => {
    setAllFiles(allFiles => ({
      ...allFiles,
      [response.video_name]: response
    }));
  };

  const getUploadParams = () => {
    return { url: `${process.env.REACT_APP_API_URL}/api/files/upload` };
  };

  const handleChangeStatus = ({ meta, remove }, status) => {
    const errorStates = [
      'error_file_size',
      'error_validation',
      'error_upload_params',
      'exception_upload',
      'error_upload'
    ];

    if (status === 'headers_received') {
      toast.success(`${meta.name} uploaded!`);
      // Note: backend emits a state change after upload is accepted, no need to do anything
      remove();
    } else if (status === 'aborted') {
      toast.warn(`${meta.name}, upload aborted...`);
    } else if (errorStates.includes(status)) {
      toast.error(`${meta.name}, upload failed... status=${status}`);
    }
  };

  const filterFilesOnType = (files, type) => {
    const filteredFiles = [];

    for (const value of Object.values(files)) {
      if (value.type === type) {
        filteredFiles.push(value);
      }
    }

    return filteredFiles;
  };

  const uploadsAsList = files => {
    return filterFilesOnType(files, 'UPLOAD');
  };

  const archiveFilesAsList = files => {
    return filterFilesOnType(files, 'ARCHIVAL_FOOTAGE');
  };

  const getVideoNames = files => {
    return files.map(f => f.video_name);
  }

  const onCompareSelectionSubmitHandler = e => {
    e.preventDefault();
    console.log('submit: ', selectedArchiveFiles);
    console.log('submit: ', selectedUploads);

    axios.post(
      `${process.env.REACT_APP_API_URL}/api/fingerprints/compare`,
      {
        query_video_names: getVideoNames(selectedUploads),
        reference_video_names: getVideoNames(selectedArchiveFiles)
      }
    )
  };

  const memoizedArchiveFiles = React.useMemo(
    () => archiveFilesAsList(allFiles),
    [allFiles]
  );

  const memoizedUploads = React.useMemo(() => uploadsAsList(allFiles), [
    allFiles
  ]);

  const styles = {
    outer: {
      display: 'flex',
      flexDirection: 'row',
      justifyContent: 'center'
    },
    inner: {
      flex: '0 0 50%'
    }
  };

  return (
    <div>
      <div className="row">
        <div className="col">
          <Dropzone
            getUploadParams={getUploadParams}
            onChangeStatus={handleChangeStatus}
            styles={{
              dropzoneActive: { borderColor: 'green' }
            }}
          />
          <ToastContainer />
        </div>
      </div>
      <div className="row mt-5">
        <div className="col">
          <div style={styles.outer}>
            <div style={styles.inner}>
              <FileTable
                caption={'Uploads'}
                data={memoizedUploads}
                onSelectedRows={setSelectedUploads}
              />
            </div>
            <div style={styles.inner}>
              <FileTable
                caption={'Reference Archive'}
                data={memoizedArchiveFiles}
                onSelectedRows={setSelectedArchiveFiles}
              />
            </div>
          </div>
          <Button variant="contained" color="primary" onClick={onCompareSelectionSubmitHandler}>
            Compute Comparisons Between Selected
          </Button>
        </div>
      </div>
    </div>
  );
}
